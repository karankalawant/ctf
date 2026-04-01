from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import random
from django.utils import timezone
from datetime import timedelta

class EmailOTP(models.Model):
    user = models.ForeignKey('CTFUser', on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))

class CTFUser(AbstractUser):
    bio = models.TextField(blank=True, default='')
    country = models.CharField(max_length=100, blank=True, default='')
    avatar_url = models.URLField(blank=True, default='')
    # Use plain IntegerField to avoid circular FK with teams app
    team_id_ref = models.IntegerField(null=True, blank=True, db_column='team_id_ref')
    is_banned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def team(self):
        if not self.team_id_ref:
            return None
        from teams.models import Team
        try:
            return Team.objects.get(pk=self.team_id_ref)
        except Team.DoesNotExist:
            return None

    @team.setter
    def team(self, value):
        self.team_id_ref = value.pk if value else None

    def get_score(self):
        from submissions.models import Submission
        solved = Submission.objects.filter(user=self, is_correct=True).select_related('challenge')
        return sum(s.challenge.get_current_points() for s in solved)

    def get_solved_count(self):
        from submissions.models import Submission
        return Submission.objects.filter(user=self, is_correct=True).count()

    def __str__(self):
        return self.username


class AdminTimeLog(models.Model):
    """Track when users access the Django admin interface"""
    user = models.ForeignKey(CTFUser, on_delete=models.CASCADE, related_name='admin_sessions')
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)  # cached duration in seconds
    
    class Meta:
        ordering = ['-login_time']
    
    def get_duration(self):
        """Get duration in seconds, or None if still active"""
        if self.logout_time:
            delta = self.logout_time - self.login_time
            return int(delta.total_seconds())
        return None
    
    def is_active(self):
        """Check if session is still active"""
        return self.logout_time is None
    
    def save(self, *args, **kwargs):
        """Update duration_seconds before saving"""
        if self.logout_time and not self.duration_seconds:
            self.duration_seconds = self.get_duration()
        super().save(*args, **kwargs)
        
        # Update CountryAdminStats after saving
        if self.user.country and self.user.country.strip() != '':
            self._update_country_stats()
    
    def _update_country_stats(self):
        """Update CountryAdminStats for the user's country"""
        from django.db.models import Count, Sum
        
        country = self.user.country
        
        # Count users in this country
        user_count = CTFUser.objects.filter(country=country).count()
        
        # Get total hours and sessions for this country
        users_in_country = CTFUser.objects.filter(country=country)
        logs = AdminTimeLog.objects.filter(
            user__in=users_in_country,
            logout_time__isnull=False
        ).aggregate(
            total_seconds=Sum('duration_seconds'),
            session_count=Count('id')
        )
        
        total_seconds = logs['total_seconds'] or 0
        total_hours = round(total_seconds / 3600, 2)
        session_count = logs['session_count'] or 0
        
        # Update or create the stats entry
        CountryAdminStats.objects.update_or_create(
            country=country,
            defaults={
                'total_hours': total_hours,
                'total_sessions': session_count,
                'user_count': user_count,
            }
        )
    
    def __str__(self):
        return f"{self.user.username} - {self.login_time.strftime('%Y-%m-%d %H:%M')}"


class CountryAdminStats(models.Model):
    """Cache aggregated admin time statistics by country"""
    country = models.CharField(max_length=100, unique=True, db_index=True)
    total_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_sessions = models.IntegerField(default=0)
    user_count = models.IntegerField(default=0)  # unique users from that country
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Country Admin Stats"
        ordering = ['-total_hours']
    
    def __str__(self):
        return f"{self.country}: {self.total_hours}h"
    
    @classmethod
    def recalculate_all(cls):
        """Recalculate all country statistics from AdminTimeLog"""
        from django.db.models import Sum, Count, Q
        
        # Get all countries with users
        countries = CTFUser.objects.filter(country__isnull=False).exclude(country='').values_list('country', flat=True).distinct()
        
        for country in countries:
            users = CTFUser.objects.filter(country=country)
            
            # Get total hours and sessions
            logs = AdminTimeLog.objects.filter(
                user__in=users,
                logout_time__isnull=False
            ).aggregate(
                total_seconds=Sum('duration_seconds'),
                session_count=Count('id')
            )
            
            total_seconds = logs['total_seconds'] or 0
            total_hours = round(total_seconds / 3600, 2)
            session_count = logs['session_count'] or 0
            user_count = users.count()
            
            cls.objects.update_or_create(
                country=country,
                defaults={
                    'total_hours': total_hours,
                    'total_sessions': session_count,
                    'user_count': user_count,
                }
            )


@receiver(post_save, sender=CTFUser)
def update_country_stats_on_user_save(sender, instance, created, **kwargs):
    """
    Signal handler to update CountryAdminStats when a user is created or country is changed.
    This ensures user_count is always up-to-date.
    """
    # Only process if user has a country set
    if not instance.country or instance.country.strip() == '':
        return
    
    from django.db.models import Count, Sum
    
    country = instance.country
    
    # Count users in this country
    user_count = CTFUser.objects.filter(country=country).count()
    
    # Get total hours and sessions for this country
    users_in_country = CTFUser.objects.filter(country=country)
    logs = AdminTimeLog.objects.filter(
        user__in=users_in_country,
        logout_time__isnull=False
    ).aggregate(
        total_seconds=Sum('duration_seconds'),
        session_count=Count('id')
    )
    
    total_seconds = logs['total_seconds'] or 0
    total_hours = round(total_seconds / 3600, 2)
    session_count = logs['session_count'] or 0
    
    # Update or create the stats entry
    stats, _ = CountryAdminStats.objects.update_or_create(
        country=country,
        defaults={
            'total_hours': total_hours,
            'total_sessions': session_count,
            'user_count': user_count,
        }
    )

