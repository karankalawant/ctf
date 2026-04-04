from django.contrib import admin
from django.db.models import Count, Max, Min
from django.utils.html import format_html
from django.urls import path
from django.template.response import TemplateResponse
from .models import CTFUser, AdminTimeLog, CountryAdminStats, LoginAttempt, SecurityLog


@admin.register(CTFUser)
class CTFUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'team_id_ref', 'is_banned', 'is_staff', 'total_time_spent', 'created_at']
    list_filter = ['is_banned', 'is_staff']
    search_fields = ['username', 'email']
    readonly_fields = ['time_spent_breakdown']
    actions = ['ban_users', 'unban_users']

    def ban_users(self, request, qs):
        qs.update(is_banned=True)

    def unban_users(self, request, qs):
        qs.update(is_banned=False)

    def _get_challenge_stats(self, user):
        """Return per-challenge duration and attempt counts for a user."""
        from submissions.models import Submission
        stats = (
            Submission.objects.filter(user=user)
            .values('challenge', 'challenge__title', 'challenge__category__name')
            .annotate(first=Min('submitted_at'), last=Max('submitted_at'), attempts=Count('id'))
            .order_by('challenge__category__name', 'challenge__title')
        )
        results = []
        for s in stats:
            delta = s['last'] - s['first']
            results.append((
                s['challenge__category__name'],
                s['challenge__title'],
                delta,
                s['attempts'],
            ))
        return results

    @staticmethod
    def _fmt_duration(td):
        total = int(td.total_seconds())
        if total < 60:
            return f"{total}s"
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        parts = []
        if h:
            parts.append(f"{h}h")
        if m:
            parts.append(f"{m}m")
        if s:
            parts.append(f"{s}s")
        return ' '.join(parts)

    def total_time_spent(self, obj):
        from datetime import timedelta
        times = self._get_challenge_stats(obj)
        total = sum((t for _, _, t, _ in times), timedelta())
        return self._fmt_duration(total)
    total_time_spent.short_description = 'Total Time'

    def time_spent_breakdown(self, obj):
        from datetime import timedelta
        times = self._get_challenge_stats(obj)
        if not times:
            return 'No submissions yet.'
        rows = ''.join(
            f'<tr><td>{cat}</td><td>{title}</td><td>{self._fmt_duration(dur)}</td><td>{attempts}</td></tr>'
            for cat, title, dur, attempts in times
        )
        total = sum((t for _, _, t, _ in times), timedelta())
        total_attempts = sum(attempts for _, _, _, attempts in times)
        return format_html(
            '<table style="border-collapse:collapse;min-width:520px">'
            '<thead><tr><th style="text-align:left;padding:4px 12px;border-bottom:2px solid #ccc">Category</th>'
            '<th style="text-align:left;padding:4px 12px;border-bottom:2px solid #ccc">Challenge</th>'
            '<th style="text-align:left;padding:4px 12px;border-bottom:2px solid #ccc">Time Spent</th>'
            '<th style="text-align:left;padding:4px 12px;border-bottom:2px solid #ccc">Attempts</th></tr></thead>'
            '<tbody>{}</tbody>'
            '<tfoot><tr><td colspan="2" style="padding:4px 12px;border-top:2px solid #ccc"><strong>Total</strong></td>'
            '<td style="padding:4px 12px;border-top:2px solid #ccc"><strong>{}</strong></td>'
            '<td style="padding:4px 12px;border-top:2px solid #ccc"><strong>{}</strong></td></tr></tfoot>'
            '</table>',
            format_html(rows),
            self._fmt_duration(total),
            total_attempts,
        )
    time_spent_breakdown.short_description = 'Time Spent Per Challenge'


@admin.register(AdminTimeLog)
class AdminTimeLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_time', 'logout_time', 'duration_display', 'is_active_display']
    list_filter = ['login_time', 'logout_time', 'user__country']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['login_time', 'duration_seconds']
    ordering = ['-login_time']
    
    def duration_display(self, obj):
        """Display formatted duration"""
        if obj.duration_seconds:
            total = obj.duration_seconds
            h, rem = divmod(total, 3600)
            m, s = divmod(rem, 60)
            parts = []
            if h:
                parts.append(f"{h}h")
            if m:
                parts.append(f"{m}m")
            if s:
                parts.append(f"{s}s")
            return ' '.join(parts) if parts else '0s'
        return '-'
    duration_display.short_description = 'Duration'
    
    def is_active_display(self, obj):
        """Show active status with color"""
        if obj.is_active():
            return format_html(
                '<span style="color: green; font-weight: bold;">● Active</span>'
            )
        return format_html(
            '<span style="color: gray;">● Closed</span>'
        )
    is_active_display.short_description = 'Status'


@admin.register(CountryAdminStats)
class CountryAdminStatsAdmin(admin.ModelAdmin):
    list_display = ['country', 'total_hours_display', 'total_sessions', 'user_count', 'last_updated']
    list_filter = ['country', 'last_updated']
    search_fields = ['country']
    readonly_fields = ['country', 'total_hours', 'total_sessions', 'user_count', 'last_updated', 'recalculate_button']
    ordering = ['-total_hours']
    
    def has_add_permission(self, request):
        """Prevent manual addition of country stats"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion for recalculation"""
        return True
    
    def total_hours_display(self, obj):
        """Display total hours with color coding"""
        hours = float(obj.total_hours)
        if hours > 100:
            color = '#d32f2f'  # Red
        elif hours > 50:
            color = '#f57c00'  # Orange
        else:
            color = '#388e3c'  # Green
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} hrs</span>',
            color,
            obj.total_hours
        )
    total_hours_display.short_description = 'Total Hours'
    
    def recalculate_button(self, obj):
        """Button to recalculate stats"""
        return format_html(
            '<button type="button" onclick="alert(\'Stats are auto-calculated. Delete and refresh to recalculate.\')">Auto-Calculated</button>'
        )
    recalculate_button.short_description = 'Calculation'
    
    def changelist_view(self, request, extra_context=None):
        """Add summary statistics to changelist"""
        from django.db.models import Sum
        
        total_hours = CountryAdminStats.objects.aggregate(Sum('total_hours'))['total_hours__sum'] or 0
        total_users = CountryAdminStats.objects.aggregate(Sum('user_count'))['user_count__sum'] or 0
        country_count = CountryAdminStats.objects.count()
        
        extra_context = extra_context or {}
        extra_context['summary'] = {
            'total_countries': country_count,
            'total_users': total_users,
            'total_hours': round(total_hours, 2),
            'avg_hours_per_country': round(total_hours / country_count, 2) if country_count > 0 else 0,
        }
        
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['username', 'ip_address', 'successful', 'timestamp']
    list_filter = ['successful', 'timestamp']
    search_fields = ['username', 'ip_address']
    readonly_fields = ['username', 'ip_address', 'user_agent', 'successful', 'timestamp']
    ordering = ['-timestamp']

    def has_add_permission(self, request):
        return False


@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'username', 'ip_address', 'short_details', 'timestamp']
    list_filter = ['event_type', 'timestamp']
    search_fields = ['username', 'ip_address', 'details']
    readonly_fields = ['event_type', 'ip_address', 'username', 'user_agent', 'details', 'timestamp']
    ordering = ['-timestamp']

    def has_add_permission(self, request):
        return False

    def short_details(self, obj):
        return obj.details[:80] + '...' if len(obj.details) > 80 else obj.details
    short_details.short_description = 'Details'
