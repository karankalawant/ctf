from django.contrib import admin
from .models import Submission

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'challenge', 'is_correct', 'ip_address', 'submitted_at']
    list_filter = ['is_correct']
    readonly_fields = ['submitted_at']
