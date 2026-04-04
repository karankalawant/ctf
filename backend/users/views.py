from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CTFUser, EmailOTP, LoginAttempt, SecurityLog
from .serializers import (UserRegistrationSerializer, UserLoginSerializer,
                           UserProfileSerializer, PublicUserSerializer)
from django.core.mail import send_mail


# ─── Rate Throttles ───

class LoginThrottle(AnonRateThrottle):
    rate = '5/min'

class RegisterThrottle(AnonRateThrottle):
    rate = '3/min'

class OTPThrottle(AnonRateThrottle):
    rate = '5/min'


# ─── Helpers ───

def get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')

def get_user_agent(request):
    return request.META.get('HTTP_USER_AGENT', '')[:500]


# ─── Registration (with honeypot) ───

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RegisterThrottle])
def register(request):
    ip = get_client_ip(request)
    ua = get_user_agent(request)

    # Honeypot check — bots fill hidden fields
    honeypot = request.data.get('website', '')
    if honeypot:
        SecurityLog.log('HONEYPOT', ip_address=ip, details=f'honeypot filled: {honeypot}')
        # Return success to not tip off the bot
        return Response({
            "message": "OTP sent to email. Please verify.",
            "user_id": 0
        }, status=201)

    s = UserRegistrationSerializer(data=request.data)
    if s.is_valid():
        user = s.save()
        user.is_active = False
        user.save()

        otp_code = EmailOTP.generate_otp()
        EmailOTP.create_for_user(user, otp_code)

        send_mail(
            subject='HackArena OTP Verification',
            message=f'Your OTP is: {otp_code}\n\nThis code expires in 5 minutes.',
            from_email='antigravityclaude02@gmail.com',
            recipient_list=[user.email],
        )

        SecurityLog.log('REGISTER', ip_address=ip, username=user.username,
                        user_agent=ua, details=f'email={user.email}')

        return Response({
            "message": "OTP sent to email. Please verify.",
            "user_id": user.id
        }, status=201)

    return Response(s.errors, status=400)


# ─── Login (with lockout + logging) ───

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
def login(request):
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    username = request.data.get('username', '')

    # Check lockout BEFORE authenticating
    if LoginAttempt.is_locked_out(username):
        SecurityLog.log('LOCKOUT', ip_address=ip, username=username,
                        user_agent=ua, details='Login blocked — account locked out')
        return Response(
            {"error": "Account temporarily locked due to too many failed attempts. Try again in 15 minutes."},
            status=429
        )

    s = UserLoginSerializer(data=request.data)
    if s.is_valid():
        user = s.validated_data['user']

        # Record successful login
        LoginAttempt.record(username=username, ip_address=ip, user_agent=ua, successful=True)
        SecurityLog.log('LOGIN_SUCCESS', ip_address=ip, username=username, user_agent=ua)

        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserProfileSerializer(user).data
        })

    # Record failed login
    LoginAttempt.record(username=username, ip_address=ip, user_agent=ua, successful=False)
    SecurityLog.log('LOGIN_FAIL', ip_address=ip, username=username,
                    user_agent=ua, details='Invalid credentials')

    # Check if this failure triggers a lockout
    if LoginAttempt.is_locked_out(username):
        SecurityLog.log('LOCKOUT', ip_address=ip, username=username,
                        user_agent=ua, details='Account locked after reaching max failed attempts')

    return Response(s.errors, status=400)


# ─── Logout ───

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logged out"})
    except Exception:
        return Response({"error": "Invalid token"}, status=400)


# ─── Profile ───

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile(request):
    if request.method == 'GET':
        return Response(UserProfileSerializer(request.user).data)
    s = UserProfileSerializer(request.user, data=request.data, partial=True)
    if s.is_valid():
        s.save()
        return Response(s.data)
    return Response(s.errors, status=400)


# ─── User Detail (public) ───

@api_view(['GET'])
@permission_classes([AllowAny])
def user_detail(request, username):
    try:
        user = CTFUser.objects.get(username=username)
        return Response(PublicUserSerializer(user).data)
    except CTFUser.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)


# ─── User List (public) ───

@api_view(['GET'])
@permission_classes([AllowAny])
def user_list(request):
    users = CTFUser.objects.filter(is_banned=False)
    return Response(PublicUserSerializer(users, many=True).data)


# ─── OTP Verification (with brute-force protection) ───

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([OTPThrottle])
def verify_otp(request):
    user_id = request.data.get("user_id")
    otp = request.data.get("otp")
    ip = get_client_ip(request)
    ua = get_user_agent(request)

    if not user_id or not otp:
        return Response({"error": "user_id and otp are required"}, status=400)

    try:
        user = CTFUser.objects.get(id=user_id)
        otp_record = EmailOTP.objects.filter(
            user=user, is_verified=False
        ).latest('created_at')
    except (CTFUser.DoesNotExist, EmailOTP.DoesNotExist):
        SecurityLog.log('OTP_FAIL', ip_address=ip, details=f'user_id={user_id} — no valid record')
        return Response({"error": "Invalid OTP"}, status=400)

    # Check if OTP is locked out
    if otp_record.is_locked():
        SecurityLog.log('OTP_LOCKOUT', ip_address=ip, username=user.username,
                        user_agent=ua, details='OTP attempts exhausted')
        return Response({"error": "Too many failed attempts. Request a new OTP."}, status=429)

    # Check if expired
    if otp_record.is_expired():
        return Response({"error": "OTP expired. Please register again."}, status=400)

    # Verify OTP (compare hashes)
    if not otp_record.check_otp(otp):
        otp_record.increment_attempts()
        SecurityLog.log('OTP_FAIL', ip_address=ip, username=user.username,
                        user_agent=ua, details=f'attempt #{otp_record.attempt_count}')

        if otp_record.is_locked():
            SecurityLog.log('OTP_LOCKOUT', ip_address=ip, username=user.username,
                            user_agent=ua, details='OTP locked after max attempts')
            return Response({"error": "Too many failed attempts. Request a new OTP."}, status=429)

        remaining = 3 - otp_record.attempt_count
        return Response({"error": f"Invalid OTP. {remaining} attempt(s) remaining."}, status=400)

    # Success!
    otp_record.is_verified = True
    otp_record.save()

    user.is_active = True
    user.save()

    SecurityLog.log('OTP_SUCCESS', ip_address=ip, username=user.username, user_agent=ua)

    refresh = RefreshToken.for_user(user)

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "message": "Account verified successfully!"
    })