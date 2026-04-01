"""
Middleware to track user access to Django admin interface
"""
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from users.models import AdminTimeLog


class AdminTrackingMiddleware(MiddlewareMixin):
    """Track admin access time for users"""
    
    def process_request(self, request):
        """Log admin access on request"""
        if request.user.is_authenticated and self._is_admin_request(request):
            # Check if user already has an active session
            active_session = AdminTimeLog.objects.filter(
                user=request.user,
                logout_time__isnull=True
            ).first()
            
            if not active_session:
                # Create new session
                AdminTimeLog.objects.create(user=request.user)
        
        return None
    
    def process_response(self, request, response):
        """Track logout from admin"""
        if request.user.is_authenticated and self._is_admin_request(request):
            # Session is still active, keep it open
            pass
        elif request.user.is_authenticated:
            # User left admin area, close the session
            from django.utils import timezone
            
            active_session = AdminTimeLog.objects.filter(
                user=request.user,
                logout_time__isnull=True
            ).first()
            
            if active_session:
                active_session.logout_time = timezone.now()
                active_session.save()
        
        return response
    
    @staticmethod
    def _is_admin_request(request):
        """Check if request is for admin interface"""
        try:
            resolved = resolve(request.path)
            return resolved.app_name == 'admin' or request.path.startswith('/admin/')
        except Exception:
            return False
