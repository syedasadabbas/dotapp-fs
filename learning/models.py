from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os
from editor.models import SubDot, Dot, Topic

# Create your models here.

def user_profile_path(instance, filename):
    # Generate file path for user profile pictures
    ext = filename.split('.')[-1]
    filename = f'{instance.user.username}_profile.{ext}'
    return os.path.join('profile_pics', filename)

class LearnerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to=user_profile_path, blank=True, null=True)
    learning_style = models.CharField(max_length=20, choices=[
        ('visual', 'Visual'),
        ('auditory', 'Auditory'),
        ('reading', 'Reading/Writing'),
        ('kinesthetic', 'Kinesthetic')
    ], default='visual')
    email_notifications = models.BooleanField(default=True)
    progress_reminders = models.BooleanField(default=True)
    public_profile = models.BooleanField(default=False)
    show_progress = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def profile_image_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        return None
        

class Progress(models.Model):
    learner = models.ForeignKey(LearnerProfile, on_delete=models.CASCADE)
    subdot = models.ForeignKey(SubDot, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent = models.DurationField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    start_time = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(default=0)

    class Meta:
        unique_together = ('learner', 'subdot')
    
    def __str__(self):
        return f"{self.learner.user.username}'s progress on {self.subdot.title}"

class Note(models.Model):
    learner = models.ForeignKey(LearnerProfile, on_delete=models.CASCADE, null=True)  # Allow null temporarily for migration
    subdot = models.ForeignKey(SubDot, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Note by {self.learner.user.username if self.learner else 'Unknown'} for {self.subdot.title}"

class Bookmark(models.Model):
    learner = models.ForeignKey(LearnerProfile, on_delete=models.CASCADE)
    subdot = models.ForeignKey(SubDot, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('learner', 'subdot')
    
class Assessment(models.Model):
    learner = models.ForeignKey(User, on_delete=models.CASCADE)
    subdot = models.ForeignKey(SubDot, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.learner.username} - {self.subdot.title}"

class AssessmentQuestion(models.Model):
    assessment = models.ForeignKey(Assessment, related_name="questions", on_delete=models.CASCADE)
    question_text = models.TextField()
    selected_answer = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=255)
    is_correct = models.BooleanField()

    def __str__(self):
        return f"Q: {self.question_text} - {self.is_correct}"

class AssessmentResult(models.Model):
    learner = models.ForeignKey(LearnerProfile, on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    score = models.FloatField()
    subdot = models.ForeignKey(SubDot, on_delete=models.CASCADE)
    total_marks = models.IntegerField(default=10)
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.learner.username} - {self.subdot.title}: {self.score}/{self.total_marks}"
    
class InstructorQuestion(models.Model):
    learner = models.ForeignKey(LearnerProfile, on_delete=models.CASCADE)
    subdot = models.ForeignKey(SubDot, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)

class NewNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Note by {self.user.username} on {self.topic.title}"

class DotProgress(models.Model):
    learner = models.ForeignKey(LearnerProfile, on_delete=models.CASCADE)
    dot = models.ForeignKey(Dot, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_subdots_completed = models.IntegerField(default=0)

    class Meta:
        unique_together = ('learner', 'dot')

    def __str__(self):
        return f"{self.learner.user.username}'s progress on {self.dot.title}"

    def update_completion(self):
        total_subdots = self.dot.subdots.count()
        completed_subdots = Progress.objects.filter(
            learner=self.learner,
            subdot__dot=self.dot,
            completed=True
        ).count()
        self.total_subdots_completed = completed_subdots
        self.completed = total_subdots == completed_subdots
        if self.completed and not self.completed_at:
            self.completed_at = timezone.now()
        self.save()

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    duration_days = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - ${self.price}"

class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='pending')

    def save(self, *args, **kwargs):
        """ Automatically set end_date based on plan duration """
        if self.plan and not self.end_date:
            self.end_date = timezone.now() + timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}'s subscription - {self.plan.name if self.plan else 'Free Trial'}"

    def is_valid(self):
        """ Check if the subscription is still active """
        return self.is_active and self.end_date > timezone.now()

class FreeTrialUsage(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dot = models.ForeignKey(Dot, on_delete=models.CASCADE)
    subdots_accessed = models.ManyToManyField(SubDot)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'dot')

    def has_free_trial_access(self):
        return self.subdots_accessed.count() < 4

    def __str__(self):
        return f"{self.user.username}'s trial usage for {self.dot.title}"