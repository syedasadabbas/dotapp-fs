import random
from django.shortcuts import render, redirect, get_object_or_404
from editor.models import SubDot
from learning.models import Assessment, AssessmentQuestion, AssessmentResult
from django.contrib.auth.decorators import login_required

@login_required
def generate_assessment(request, subdot_id):
    subdot = get_object_or_404(SubDot, id=subdot_id)
    content_items = list(subdot.contents.all())  # Adjust if your model differs

    random.shuffle(content_items)
    number_of_questions = min(len(content_items), 10)
    selected_items = content_items[:number_of_questions]

    if request.method == "POST":
        learner = request.user
        assessment = Assessment.objects.create(learner=learner, subdot=subdot)
        score = 0

        for item in selected_items:
            selected_answer = request.POST.get(f"question_{item.id}", "")
            is_correct = (selected_answer == item.correct_answer)
            if is_correct:
                score += 1

            AssessmentQuestion.objects.create(
                assessment=assessment,
                question_text=item.question,
                selected_answer=selected_answer,
                correct_answer=item.correct_answer,
                is_correct=is_correct
            )

        result = AssessmentResult.objects.create(
            learner=learner.learnerprofile,
            subdot=subdot,
            score=score,
            total_marks=10
        )
        return redirect("assessment_result", result_id=result.id)

    return render(request, "learning/assessment.html", {
        "subdot": subdot,
        "questions": selected_items
    })

@login_required
def assessment_result(request, result_id):
    result = get_object_or_404(AssessmentResult, id=result_id)
    return render(request, "learning/assessment_result.html", {"result": result})
