from django.contrib import admin
from .models import Challenge, Category, Hint, HintUnlock, Event

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'description']
    search_fields = ['name']

@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'difficulty', 'points', 'is_active', 'is_dynamic']
    list_filter = ['category', 'difficulty', 'is_active']
    search_fields = ['title', 'author']

@admin.register(Hint)
class HintAdmin(admin.ModelAdmin):
    list_display = ['challenge', 'cost', 'order']

@admin.register(HintUnlock)
class HintUnlockAdmin(admin.ModelAdmin):
    list_display = ['user', 'hint', 'unlocked_at']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    fieldsets = (
        ('Event Information', {
            'fields': ('name', 'is_active')
        }),
        ('Timer Settings', {
            'fields': ('start_date', 'end_date'),
            'description': 'Set the start and end dates for the CTF event countdown timer'
        }),
    )