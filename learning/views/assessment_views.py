import openai
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from editor.models import SubDot, Dot
from learning.models import Assessment, AssessmentQuestion, AssessmentResult
from django.contrib.auth.decorators import login_required
from learning.models import LearnerProfile
from django.conf import settings
import json
from django.utils import timezone  # Change this import
from decouple import config 
import logging
from django.db import transaction  # Add this import

logger = logging.getLogger(__name__)

openai.api_key = config('OPENAI_API_KEY')
@login_required
def start_assessment(request, dot_id):
    try:
        with transaction.atomic():  # Add transaction handling
            dot = get_object_or_404(Dot, id=dot_id)
            subdots = SubDot.objects.filter(dot=dot)
            user = request.user
            learner_profile = request.user.learnerprofile

            # Get the first subdot
            first_subdot = subdots.first()
            if not first_subdot:
                return JsonResponse({
                    'success': False,
                    'error': 'No SubDots found for this Dot.'
                })

            # First, try to get an existing incomplete assessment
            try:
                assessment = Assessment.objects.get(
                    subdot=first_subdot,
                    learner=user,
                    completed=False
                )
                # If assessment exists and has questions, return those questions
                existing_questions = assessment.questions.all()
                if existing_questions.exists():
                    return JsonResponse({
                        'success': True,
                        'questions': [{
                            'id': q.id,
                            'question_text': q.question_text,
                            'option_a': q.option_a,
                            'option_b': q.option_b,
                            'option_c': q.option_c,
                            'option_d': q.option_d
                        } for q in existing_questions]
                    })
            except Assessment.DoesNotExist:
                # If no assessment exists, we'll create one later
                assessment = None

            if request.method == "GET":
                try:
                    # Collect content for questions
                    content_parts = []
                    if dot.description:
                        content_parts.append(f"Main Topic: {dot.title}\n{dot.description}")
                    
                    for subdot in subdots:
                        if subdot.content:
                            content_parts.append(f"Subtopic: {subdot.title}\n{subdot.content}")
                            for topic in subdot.topics.all():
                                if topic.content:
                                    content_parts.append(f"Topic: {topic.title}\n{topic.content}")

                    content = '\n\n'.join(filter(None, content_parts))

                    if not content.strip():
                        return JsonResponse({
                            'success': False,
                            'error': 'No content available for generating questions.'
                        })

                    # Generate questions using OpenAI
                    prompt = f"""
                    Based on the following educational content, generate 6 multiple-choice questions. 
                    Each question should have 4 options (A, B, C, D) and one correct answer.
                    
                    Content:
                    {content}

                    Return the questions in this exact JSON format:
                    [
                        {{
                            "question": "Question text here",
                            "options": [
                                "Option A text",
                                "Option B text",
                                "Option C text",
                                "Option D text"
                            ],
                            "correctAnswer": "A"
                        }}
                    ]
                    """

                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[{
                            "role": "system",
                            "content": "You are an educational assessment expert."
                        }, {
                            "role": "user",
                            "content": prompt
                        }],
                        max_tokens=2000,
                        temperature=0.7
                    )

                    questions_json = response['choices'][0]['message']['content']
                    questions_data = json.loads(questions_json)

                    # If we have an existing assessment, delete its questions
                    if assessment:
                        assessment.questions.all().delete()
                    else:
                        # Create new assessment if none exists
                        assessment = Assessment.objects.create(
                            subdot=first_subdot,
                            learner=user,
                            created_at=timezone.now(),
                            completed=False
                        )

                    # Create new questions
                    questions = []
                    for q_data in questions_data:
                        new_question = AssessmentQuestion.objects.create(
                            assessment=assessment,
                            question_text=q_data['question'],
                            option_a=q_data['options'][0],
                            option_b=q_data['options'][1],
                            option_c=q_data['options'][2],
                            option_d=q_data['options'][3],
                            correct_answer=q_data['correctAnswer'].strip().upper()
                        )
                        questions.append(new_question)

                    return JsonResponse({
                        'success': True,
                        'questions': [{
                            'id': q.id,
                            'question_text': q.question_text,
                            'option_a': q.option_a,
                            'option_b': q.option_b,
                            'option_c': q.option_c,
                            'option_d': q.option_d
                        } for q in questions]
                    })

                except Exception as e:
                    logger.error(f"Error generating questions: {str(e)}")
                    return JsonResponse({
                        'success': False,
                        'error': 'Failed to generate questions. Please try again later.'
                    })

            elif request.method == "POST":
                if not assessment:
                    return JsonResponse({
                        'success': False,
                        'error': 'No active assessment found.'
                    })

                questions = assessment.questions.all()
                score = 0

                for question in questions:
                    selected_answer = request.POST.get(f"question_{question.id}", "")
                    is_correct = (selected_answer == question.correct_answer)
                    if is_correct:
                        score += 1

                total_marks = questions.count()

                # Create result
                result = AssessmentResult.objects.create(
                    learner=learner_profile,
                    assessment=assessment,
                    score=score,
                    total_marks=total_marks,
                    subdot=first_subdot
                )

                # Mark assessment as completed
                assessment.completed = True
                assessment.completed_at = timezone.now()
                assessment.save()

                return redirect('assessment_result', result.id)

    except Exception as e:
        logger.error(f"Error in start_assessment: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        })


@login_required
def assessment_result(request, result_id):
    result = get_object_or_404(AssessmentResult, id=result_id, learner=request.user.learnerprofile)
    questions = result.assessment.questions.all()

    # Get each question with selected answer and correctness
    question_details = []
    for question in questions:
        selected_answer = request.session.get(f"selected_answer_{question.id}", None)
        is_correct = (selected_answer == question.correct_answer)
        question_details.append({
            'question_text': question.question_text,
            'selected_answer': selected_answer,
            'correct_answer': question.correct_answer,
            'is_correct': is_correct
        })

    return render(request, "learning/assessment_result.html", {
        "result": result,
        "questions": question_details
    })
