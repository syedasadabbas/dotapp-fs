from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from learning.models import Progress, DotProgress, Bookmark
from editor.models import SubDot
from .utils import calculate_dot_progress
from learning.forms import InstructorQuestionForm
from django.views.decorators.http import require_http_methods

@login_required
def subdot_detail(request, subdot_id):
    subdot = get_object_or_404(SubDot, id=subdot_id)
    learner = request.user.learnerprofile

    progress, created = Progress.objects.get_or_create(learner=learner, subdot=subdot)

    next_subdot = SubDot.objects.filter(dot=subdot.dot, id__gt=subdot.id).order_by('id').first()
    previous_subdot = SubDot.objects.filter(dot=subdot.dot, id__lt=subdot.id).order_by('-id').first()

    dot_progress = calculate_dot_progress(learner, subdot.dot)
    if dot_progress == 100:
        dp, _ = DotProgress.objects.get_or_create(learner=learner, dot=subdot.dot)
        dp.completed = True
        dp.save()

    notes = subdot.note_set.filter(learner=learner).order_by('-updated_at')
    is_bookmarked = Bookmark.objects.filter(learner=learner, subdot=subdot).exists()
    track = subdot.dot.track
    topics = subdot.topics.all()

    topic_audio = []
    topic_timestamps = None
    if topics.exists():
        for topic in topics:
            if topic.audio:
                topic_audio = topic.audio.url
                topic_timestamps = topic.timestamps
                break

    context = {
        'subdot': subdot,
        'track': track,
        'progress': progress,
        'is_bookmarked': is_bookmarked,
        'next_subdot': next_subdot,
        'previous_subdot': previous_subdot,
        'dot_progress': dot_progress,
        'notes': notes,
        'topics': topics,
        'topic_audio': topic_audio,
        'topic_timestamps': topic_timestamps
    }
    return render(request, 'learning/subdot_detail.html', context)

@login_required
@require_http_methods(["POST"])
def toggle_bookmark(request, subdot_id):
    try:
        learner = request.user.learnerprofile
        subdot = get_object_or_404(SubDot, id=subdot_id)
        
        bookmark, created = Bookmark.objects.get_or_create(learner=learner, subdot=subdot)
        
        if not created:
            bookmark.delete()
            message = 'Bookmark removed successfully!'
            is_bookmarked = False
        else:
            message = 'Bookmark added successfully!'
            is_bookmarked = True
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': message,
                'is_bookmarked': is_bookmarked
            })
        else:
            messages.success(request, message)
            return redirect('subdot_detail', subdot_id=subdot_id)
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
        else:
            messages.error(request, f'Error: {str(e)}')
            return redirect('subdot_detail', subdot_id=subdot_id)

@login_required
def ask_instructor(request, subdot_id):
    if request.method == 'POST':
        form = InstructorQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.learner = request.user.learnerprofile
            question.subdot_id = subdot_id
            question.save()
            messages.success(request, 'Question submitted to instructor!')
    return redirect('subdot_detail', subdot_id=subdot_id)
