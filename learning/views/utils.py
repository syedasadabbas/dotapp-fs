from learning.models import Progress

def calculate_dot_progress(learner, dot):
    """Calculate the progress percentage for a dot based on completed subdots."""
    total_subdots = dot.subdots.count()
    if total_subdots == 0:
        return 0

    completed_subdots = Progress.objects.filter(
        learner=learner,
        subdot__dot=dot,
        completed=True
    ).count()

    # Return just a number or a dict with more info—your choice.
    return int((completed_subdots / total_subdots) * 100)

def format_timedelta(td):
    """Convert a Python timedelta to a readable string (e.g. '1h 30m')."""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"
