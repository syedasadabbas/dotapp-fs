from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from editor.models import Track, Dot, SubDot
from learning.models import Progress, DotProgress, Bookmark
from .utils import calculate_dot_progress
from learning.forms import InstructorQuestionForm
from django.views.decorators.http import require_http_methods

@login_required
def subdot_detail(request, subdot_id):
    subdot = get_object_or_404(SubDot, id=subdot_id)
    dot = subdot.dot
    track = dot.track
    learner = request.user.learnerprofile
    
    # Get the tracks we want to check
    frontend_track = Track.objects.filter(title__icontains='Frontend Developer').first()
    ai_track = Track.objects.filter(title__icontains='AI Engineer').first()
    ai_intro_dot = ai_track.dots.filter(title__icontains='Introduction').first() if ai_track else None

    print(f"Current track: {track.title}, Current dot: {dot.title}")
    print(f"Frontend track found: {frontend_track.title if frontend_track else None}")
    print(f"AI track found: {ai_track.title if ai_track else None}")
    print(f"AI intro dot found: {ai_intro_dot.title if ai_intro_dot else None}")
    
    # Determine if user has access
    has_access = False
    
    if hasattr(request.user, 'subscription'):
        has_access = True
    elif frontend_track and track.id == frontend_track.id and dot.title.lower() == 'internet':
        has_access = True
    elif ai_track and track.id == ai_track.id and dot.id == ai_intro_dot.id:
        has_access = True
    
    print(f"Has access: {has_access}")
    
    progress, created = Progress.objects.get_or_create(learner=learner, subdot=subdot)

    next_subdot = SubDot.objects.filter(dot=subdot.dot, id__gt=subdot.id).order_by('id').first()
    prev_subdot = SubDot.objects.filter(dot=subdot.dot, id__lt=subdot.id).order_by('-id').first()

    dot_progress = calculate_dot_progress(learner, subdot.dot)
    if dot_progress == 100:
        dp, _ = DotProgress.objects.get_or_create(learner=learner, dot=subdot.dot)
        dp.completed = True
        dp.save()

    notes = subdot.note_set.filter(learner=learner).order_by('-updated_at')
    is_bookmarked = Bookmark.objects.filter(learner=learner, subdot=subdot).exists()
    
    # Get all topics for this subdot
    topics = subdot.topics.all()  # Removed order_by('order') since there's no order field
    
    # Initialize variables for audio and timestamps
    topic_audio = None
    topic_timestamps = None
    
    # Find the first topic with audio and timestamps
    for topic in topics:
        if topic.audio:
            topic_audio = topic.audio.url
            topic_timestamps = topic.timestamps
            break

    context = {
        'subdot': subdot,
        'track': track,
        'dot': dot,
        'next_subdot': next_subdot,
        'prev_subdot': prev_subdot,
        'progress': progress,
        'dot_progress': dot_progress,
        'notes': notes,
        'is_bookmarked': is_bookmarked,
        'topics': topics,
        'topic_audio': topic_audio,
        'topic_timestamps': topic_timestamps,
        'has_access': has_access
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
