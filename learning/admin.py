from django.contrib import admin
from .models import (LearnerProfile, Progress, Note, NewNote, Bookmark,
                     SubscriptionPlan, UserSubscription, FreeTrialUsage)

# Register your models here.

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date', 'is_active', 'payment_status')
    list_filter = ('is_active', 'payment_status')
    search_fields = ('user__username',)

@admin.register(FreeTrialUsage)
class FreeTrialUsageAdmin(admin.ModelAdmin):
    list_display = ('user', 'dot', 'get_subdots_count', 'created_at')
    search_fields = ('user__username', 'dot__title')
    
    def get_subdots_count(self, obj):
        return obj.subdots_accessed.count()
    get_subdots_count.short_description = 'Subdots Accessed'

admin.site.register(LearnerProfile)
admin.site.register(Progress)
admin.site.register(Note)
admin.site.register(NewNote)
admin.site.register(Bookmark)
