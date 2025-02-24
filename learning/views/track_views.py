from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from editor.models import Track, Dot
from learning.models import LearnerProfile
from .utils import calculate_dot_progress

@login_required
def track_list(request):
    tracks = Track.objects.all()
    learner = request.user.learnerprofile
    dot_progress = {}

    for track in tracks:
        for dot in track.dots.all():
            dot_progress[dot.id] = calculate_dot_progress(learner, dot)

    return render(request, 'learning/track_list.html', {
        'tracks': tracks,
        'dot_progress': dot_progress,
    })

@login_required
def track_detail(request, track_id):
    track = get_object_or_404(Track, id=track_id)
    dots = track.dot_set.all().order_by('order')
    learner = request.user.learnerprofile

    dot_progress = {}
    total_time_spent = timezone.timedelta()

    for dot in dots:
        progress = calculate_dot_progress(learner, dot)
        dot_progress[dot.id] = progress

        # If you store time_spent in progress, handle that here:
        if progress and isinstance(progress, dict) and progress.get('time_spent'):
            total_time_spent += progress['time_spent']

    total_dots = dots.count()
    completed_dots = sum(1 for p in dot_progress.values() if p and p['percentage'] == 100)
    track_stats = {
        'total_dots': total_dots,
        'completed_dots': completed_dots,
        'completion_percentage': (completed_dots / total_dots * 100) if total_dots > 0 else 0
    }

    return render(request, 'learning/track_detail.html', {
        'track': track,
        'dots': dots,
        'dot_progress': dot_progress,
        'total_time_spent': total_time_spent,
        'track_stats': track_stats,
    })

@login_required
def track(request):
    # "track" view that filters by learner
    user_tracks = Track.objects.filter(learner=request.user).order_by('-created_at')

    tracks_with_progress = []
    for track_obj in user_tracks:
        dots = track_obj.dots.all()
        total_dots = dots.count()
        completed_dots = dots.filter(completed=True).count()
        progress = (completed_dots / total_dots * 100) if total_dots > 0 else 0

        description = track_obj.description if track_obj.description else "No description provided."
        tracks_with_progress.append({
            'track': track_obj,
            'total_dots': total_dots,
            'completed_dots': completed_dots,
            'progress': progress,
            'description': description
        })

    return render(request, 'learning/track.html', {
        'tracks_with_progress': tracks_with_progress
    })
