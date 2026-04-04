"""
Security middleware for the CTF platform.
Adds security response headers and monitors for suspicious request patterns.
"""
import logging
from django.utils.deprecation import MiddlewareMixin

security_logger = logging.getLogger('security')


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add comprehensive security headers to all responses."""

    def process_response(self, request, response):
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

        # HSTS (force HTTPS) — active in all environments, browsers will enforce only over HTTPS
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'

        # XSS Protection (legacy, but still useful)
        response['X-XSS-Protection'] = '1; mode=block'

        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions Policy (disable unused browser features)
        response['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), '
            'payment=(), usb=(), magnetometer=(), gyroscope=()'
        )

        return response


class RequestMonitorMiddleware(MiddlewareMixin):
    """Monitor requests for suspicious patterns and log them."""

    SUSPICIOUS_PATTERNS = [
        '../',       # Path traversal
        '..\\',      # Path traversal (Windows)
        '<script',   # XSS attempt
        'UNION SELECT',  # SQL injection
        'DROP TABLE',    # SQL injection
        'OR 1=1',        # SQL injection
        'eval(',         # Code injection
        '__import__',    # Python injection
    ]

    def process_request(self, request):
        path = request.path.lower()
        query = request.META.get('QUERY_STRING', '').lower()
        full = path + '?' + query

        # Check for suspicious patterns
        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern.lower() in full:
                ip = self._get_ip(request)
                ua = request.META.get('HTTP_USER_AGENT', '')[:200]
                security_logger.warning(
                    f"SUSPICIOUS_REQUEST | ip={ip} path={request.path} "
                    f"pattern={pattern} ua={ua}"
                )
                # Don't block — just log. The ORM/framework handles actual protection.
                break

        return None

    @staticmethod
    def _get_ip(request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')
