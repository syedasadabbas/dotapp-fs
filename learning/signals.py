from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import LearnerProfile

@receiver(post_save, sender=User)
def create_learner_profile(sender, instance, created, **kwargs):
    """Create a LearnerProfile for every new user"""
    if created:
        LearnerProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_learner_profile(sender, instance, **kwargs):
    """Save the LearnerProfile whenever the user is saved"""
    try:
        instance.learnerprofile.save()
    except LearnerProfile.DoesNotExist:
        LearnerProfile.objects.create(user=instance)
