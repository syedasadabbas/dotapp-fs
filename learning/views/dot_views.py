from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from editor.models import Track, Dot
from django.db.models import Count, Q

@login_required
def dot_detail(request, track_id, dot_id):
    track = get_object_or_404(Track, id=track_id)
    dot = get_object_or_404(Dot, track=track, id=dot_id)
    
    # Get the tracks we want to check
    frontend_track = Track.objects.filter(title__icontains='Frontend Developer').first()
    ai_track = Track.objects.filter(title__icontains='AI Engineer').first()
    ai_intro_dot = ai_track.dots.filter(title__icontains='Introduction').first() if ai_track else None

    # Determine if user has access
    has_access = False
    
    if hasattr(request.user, 'subscription'):
        has_access = True
    elif frontend_track and track.id == frontend_track.id and dot.title.lower() == 'internet':
        has_access = True
    elif ai_track and track.id == ai_track.id and dot.id == ai_intro_dot.id:
        has_access = True
    
    learner = request.user.learnerprofile

    subdots = dot.subdots.all().order_by('order')
    context = {
        'track': track,
        'dot': dot,
        'subdots': subdots,
        'learner': learner,
        'has_access': has_access
    }
    return render(request, 'learning/dot_detail.html', context)
