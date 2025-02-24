from django.contrib import admin
from .models import LearnerProfile, Progress, Note, NewNote, Bookmark

# Register your models here.
admin.site.register(LearnerProfile)
admin.site.register(Progress)
admin.site.register(Note)
admin.site.register(NewNote)
admin.site.register(Bookmark)
