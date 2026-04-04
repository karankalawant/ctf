from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import random
import hashlib
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


class EmailOTP(models.Model):
    user = models.ForeignKey('CTFUser', on_delete=models.CASCADE)
    otp_hash = models.CharField(max_length=64)  # SHA-256 hash, NOT plaintext
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    attempt_count = models.PositiveIntegerField(default=0)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def is_locked(self):
        max_attempts = getattr(settings, 'OTP_MAX_ATTEMPTS', 3)
        return self.attempt_count >= max_attempts

    def increment_attempts(self):
        self.attempt_count += 1
        self.save(update_fields=['attempt_count'])

    def check_otp(self, raw_otp):
        """Compare submitted OTP against stored hash."""
        return self._hash_otp(raw_otp) == self.otp_hash

    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))

    @staticmethod
    def _hash_otp(raw_otp):
        return hashlib.sha256(str(raw_otp).encode()).hexdigest()

    @classmethod
    def create_for_user(cls, user, raw_otp):
        """Create an OTP record with the hashed OTP."""
        return cls.objects.create(
            user=user,
            otp_hash=cls._hash_otp(raw_otp),
        )


class LoginAttempt(models.Model):
    """Track login attempts for account lockout and security monitoring."""
    username = models.CharField(max_length=150, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    successful = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['username', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]

    def __str__(self):
        status = '✓' if self.successful else '✗'
        return f"{status} {self.username} from {self.ip_address} at {self.timestamp}"

    @classmethod
    def is_locked_out(cls, username):
        """Check if username is locked out due to too many failed attempts."""
        max_attempts = getattr(settings, 'ACCOUNT_LOCKOUT_ATTEMPTS', 5)
        lockout_duration = getattr(settings, 'ACCOUNT_LOCKOUT_DURATION', timedelta(minutes=15))
        cutoff = timezone.now() - lockout_duration

        recent_failures = cls.objects.filter(
            username=username,
            successful=False,
            timestamp__gte=cutoff,
        ).count()

        return recent_failures >= max_attempts

    @classmethod
    def record(cls, username, ip_address, user_agent='', successful=False):
        return cls.objects.create(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            successful=successful,
        )


class SecurityLog(models.Model):
    """General security event log for monitoring and intrusion detection."""
    EVENT_TYPES = [
        ('LOGIN_FAIL', 'Failed Login'),
        ('LOGIN_SUCCESS', 'Successful Login'),
        ('LOCKOUT', 'Account Locked Out'),
        ('OTP_FAIL', 'Failed OTP Verification'),
        ('OTP_LOCKOUT', 'OTP Locked Out'),
        ('OTP_SUCCESS', 'OTP Verified'),
        ('REGISTER', 'Registration'),
        ('HONEYPOT', 'Honeypot Triggered'),
        ('RATE_LIMIT', 'Rate Limit Hit'),
        ('SUSPICIOUS', 'Suspicious Activity'),
        ('TOKEN_MISUSE', 'Token Misuse'),
    ]

    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    username = models.CharField(max_length=150, blank=True, default='')
    user_agent = models.TextField(blank=True, default='')
    details = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]

    def __str__(self):
        return f"[{self.event_type}] {self.username or 'anon'} from {self.ip_address} at {self.timestamp}"

    @classmethod
    def log(cls, event_type, ip_address=None, username='', user_agent='', details=''):
        import logging
        logger = logging.getLogger('security')

        level = logging.WARNING if event_type in (
            'LOGIN_FAIL', 'LOCKOUT', 'OTP_FAIL', 'OTP_LOCKOUT',
            'HONEYPOT', 'RATE_LIMIT', 'SUSPICIOUS', 'TOKEN_MISUSE'
        ) else logging.INFO

        logger.log(level, f"{event_type} | user={username} ip={ip_address} | {details}")

        return cls.objects.create(
            event_type=event_type,
            ip_address=ip_address,
            username=username,
            user_agent=user_agent,
            details=details,
        )

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

