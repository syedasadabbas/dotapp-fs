from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from editor.models import Track, Dot
from .utils import calculate_dot_progress

@login_required
def dot_detail(request, track_id, dot_id):
    track = get_object_or_404(Track, id=track_id)
    dot = get_object_or_404(Dot, track=track, id=dot_id)
    learner = request.user.learnerprofile

    subdots = dot.subdots.all().order_by('order')
    progress = calculate_dot_progress(learner, dot)

    context = {
        'track': track,
        'dot': dot,
        'subdots': subdots,
        'progress': progress,
    }
    return render(request, 'learning/dot_detail.html', context)
