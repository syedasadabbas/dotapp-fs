from django.contrib import admin
from .models import Track, Dot, SubDot, Topic
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
    list_display = ['title', 'subdot', 'created_by', 'has_content', 'has_code', 'has_image', 'has_audio']
    list_filter = ['subdot', 'created_by']
    search_fields = ['title', 'content']
    readonly_fields = ['created_by']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['title', 'subdot', 'order']
        }),
        ('Content', {
            'fields': ['content', 'code'],
            'classes': ['collapse', 'open'],
        }),
        ('Media', {
            'fields': ['image', 'audio', 'timestamps'],
            'classes': ['collapse', 'open'],
        }),
        ('Metadata', {
            'fields': ['created_by'],
            'classes': ['collapse'],
        }),
    ]
    
    def has_content(self, obj):
        return bool(obj.content)
    has_content.boolean = True
    has_content.short_description = 'Has Text'
    
    def has_code(self, obj):
        return bool(obj.code)
    has_code.boolean = True
    has_code.short_description = 'Has Code'
    
    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = 'Has Image'
    
    def has_audio(self, obj):
        return bool(obj.audio)
    has_audio.boolean = True
    has_audio.short_description = 'Has Audio'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields
        return []  # when creating a new object

admin.site.register(Track, TrackAdmin)
admin.site.register(Dot, DotAdmin)
admin.site.register(SubDot, SubDotAdmin)
admin.site.register(Topic, TopicAdmin)
