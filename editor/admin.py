from django.contrib import admin
from .models import OTP, Track, Dot, SubDot, Topic
from .forms import TrackForm, DotForm, SubDotForm, TopicForm

# Register your models here.

class TrackAdmin(admin.ModelAdmin):
    form = TrackForm

class DotAdmin(admin.ModelAdmin):
    form = DotForm

class SubDotAdmin(admin.ModelAdmin):
    form = SubDotForm

class TopicAdmin(admin.ModelAdmin):
    form = TopicForm

admin.site.register(Track, TrackAdmin)
admin.site.register(Dot, DotAdmin)
admin.site.register(SubDot, SubDotAdmin)
admin.site.register(Topic, TopicAdmin)

admin.site.register(OTP)
