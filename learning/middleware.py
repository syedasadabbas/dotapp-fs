from django.contrib.auth.models import User
from .models import LearnerProfile

class EnsureLearnerProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                # Try to access the learner profile
                _ = request.user.learnerprofile
            except User.learnerprofile.RelatedObjectDoesNotExist:
                # If it doesn't exist, create it
                LearnerProfile.objects.create(user=request.user)
        
        response = self.get_response(request)
        return response
