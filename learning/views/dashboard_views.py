from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from learning.models import LearnerProfile, Progress, Note, Bookmark, AssessmentResult
from editor.models import Track, SubDot

@login_required(login_url='/learning/login/')
def dashboard(request):
    learner, created = LearnerProfile.objects.get_or_create(user=request.user)
    tracks = Track.objects.all()

    # Calculate progress for each track
    track_progress = {}
    for track in tracks:
        dots = track.dots.all()
        total_subdots = sum(dot.subdots.count() for dot in dots)
        completed_subdots = Progress.objects.filter(
            learner=learner,
            subdot__dot__track=track,
            completed=True
        ).count()

        progress_percentage = (completed_subdots / total_subdots) * 100 if total_subdots > 0 else 0

        track_progress[track.id] = {
            'track': track,
            'total': total_subdots,
            'completed': completed_subdots,
            'percentage': round(progress_percentage, 1),
            'is_completed': progress_percentage == 100
        }

    recent_notes = Note.objects.filter(learner=learner).order_by('-created_at')[:5]
    recent_activities = Progress.objects.filter(learner=learner).order_by('-last_accessed')[:5]
    completed_dots = Progress.objects.filter(
        learner=learner,
        completed=True
    ).select_related('subdot__dot').order_by('-completed_at')[:5]
    bookmarked_subdots = SubDot.objects.filter(bookmark__learner=learner)
    user_results = AssessmentResult.objects.filter(learner=learner.user.learnerprofile).order_by('-completed_at')

    context = {
        'tracks': tracks,
        'track_progress': track_progress,
        'recent_notes': recent_notes,
        'bookmarked_subdots': bookmarked_subdots,
        'recent_activities': recent_activities,
        'completed_dots': completed_dots,
        'user_results': user_results,
    }
    return render(request, 'learning/dashboard.html', context)
