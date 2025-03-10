from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now

class Editor(AbstractUser):
    subscribed_dots = models.ManyToManyField('Dot', blank=True, related_name='subscribed_editors')
    is_approved = models.BooleanField(default=False)
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='editor_set',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups'
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='editor_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    def __str__(self):
        return self.username

class Track(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(default=now)
    created_by = models.ForeignKey(Editor, on_delete=models.CASCADE, null=True, blank=True, related_name='created_tracks')

    def get_completion_status(self, learner):
        total_dots = self.dots.count()
        if total_dots == 0:
            return 0
        completed_dots = sum(1 for dot in self.dots.all() if dot.is_completed(learner))
        return (completed_dots / total_dots) * 100

    def is_completed(self, learner):
        return all(dot.is_completed(learner) for dot in self.dots.all())

    def __str__(self):
        return self.title

class Dot(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name="dots")
    title = models.CharField(max_length=200)
    order = models.IntegerField(default=1)
    created_by = models.ForeignKey(Editor, on_delete=models.CASCADE, null=True, blank=True, related_name='created_dots')

    def get_completion_status(self, learner):
        total_subdots = self.subdots.count()
        if total_subdots == 0:
            return 0
        completed_subdots = sum(1 for subdot in self.subdots.all() if subdot.is_completed(learner))
        return (completed_subdots / total_subdots) * 100

    def is_completed(self, learner):
        return all(subdot.is_completed(learner) for subdot in self.subdots.all())

    def __str__(self):
        return self.title

class SubDot(models.Model):
    dot = models.ForeignKey(Dot, on_delete=models.CASCADE, related_name="subdots")
    title = models.CharField(max_length=200)
    content = models.TextField(default="No content available")
    code_snippet = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    order = models.IntegerField(default=1)
    created_by = models.ForeignKey(Editor, on_delete=models.CASCADE, null=True, blank=True, related_name='created_subdots')

    def is_completed(self, learner):
        try:
            progress = Progress.objects.get(learner=learner, subdot=self)
            return progress.completed
        except Progress.DoesNotExist:
            return False

    def __str__(self):
        return self.title

class Topic(models.Model):
    subdot = models.ForeignKey(SubDot, related_name='topics', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)
    code = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    audio = models.FileField(upload_to='audio/', blank=True, null=True)
    timestamps = models.JSONField(blank=True, null=True)
    created_by = models.ForeignKey(Editor, on_delete=models.CASCADE, null=True, blank=True, related_name='created_topics')
    order = models.IntegerField(default=1)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['order']

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.TextField()

class PaymentMethod(models.Model):
    method_name = models.CharField(max_length=50)
    details = models.TextField()

class Subscription(models.Model):
    editor = models.ForeignKey(Editor, on_delete=models.CASCADE)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()

class Earnings(models.Model):
    editor = models.ForeignKey(Editor, on_delete=models.CASCADE)
    learner = models.ForeignKey(Editor, on_delete=models.CASCADE, related_name='learner_earnings')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)