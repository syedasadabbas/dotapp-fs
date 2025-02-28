import json
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from learning.models import Progress, DotProgress
from editor.models import SubDot
from .utils import calculate_dot_progress

@login_required
@require_http_methods(["POST"])
def mark_completed(request, subdot_id):
    subdot = get_object_or_404(SubDot, id=subdot_id)
    learner = request.user.learnerprofile

    progress, created = Progress.objects.get_or_create(learner=learner, subdot=subdot)
    progress.completed = not progress.completed
    if progress.completed:
        progress.completed_at = timezone.now()
    progress.save()

    dot_progress = calculate_dot_progress(learner, subdot.dot)
    if dot_progress == 100:
        dot_progress_obj, _ = DotProgress.objects.get_or_create(learner=learner, dot=subdot.dot)
        dot_progress_obj.completed = True
        dot_progress_obj.completed_at = timezone.now()
        dot_progress_obj.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'completed': progress.completed,
            'dot_progress': dot_progress
        })
    return redirect('subdot_detail', subdot_id=subdot_id)

@login_required
def progress_view(request):
    from editor.models import Track
    learner = request.user.learnerprofile
    tracks = Track.objects.all()

    total_subdots = SubDot.objects.count()
    completed_subdots = Progress.objects.filter(learner=learner, completed=True).count()
    overall_progress = (completed_subdots / total_subdots * 100) if total_subdots > 0 else 0

    tracks_progress = []
    for track in tracks:
        total_track_subdots = SubDot.objects.filter(dot__track=track).count()
        completed_track_subdots = Progress.objects.filter(
            learner=learner,
            subdot__dot__track=track,
            completed=True
        ).count()

        track_progress = (completed_track_subdots / total_track_subdots * 100) if total_track_subdots > 0 else 0
        tracks_progress.append({
            'title': track.title,
            'progress': track_progress,
            'completed_dots': completed_track_subdots,
            'total_dots': total_track_subdots
        })

    recent_achievements = Progress.objects.filter(
        learner=learner, completed=True
    ).order_by('-completed_at')[:5].select_related('subdot', 'subdot__dot')

    achievements_data = []
    for achievement in recent_achievements:
        achievements_data.append({
            'title': achievement.subdot.title,
            'description': f"Completed from {achievement.subdot.dot.title}",
            'date': achievement.completed_at
        })

    context = {
        'overall_progress': overall_progress,
        'completed_dots': completed_subdots,
        'total_dots': total_subdots,
        'tracks': tracks_progress,
        'recent_achievements': achievements_data
    }
    return render(request, 'learning/progress.html', context)

@require_http_methods(["POST"])
@login_required
def update_progress(request, subdot_id):
    try:
        data = json.loads(request.body)
        time_spent = data.get('time_spent')

        if time_spent is not None:
            learner = request.user.learnerprofile
            subdot = get_object_or_404(SubDot, id=subdot_id)
            progress = Progress.objects.get_or_create(learner=learner, subdot=subdot)[0]

            time_spent_delta = timezone.timedelta(seconds=int(time_spent))
            if progress.time_spent:
                progress.time_spent += time_spent_delta
            else:
                progress.time_spent = time_spent_delta
            progress.save()

            return JsonResponse({'success': True, 'time_spent': str(progress.time_spent)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
