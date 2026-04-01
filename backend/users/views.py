from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CTFUser
from .serializers import (UserRegistrationSerializer, UserLoginSerializer,
                           UserProfileSerializer, PublicUserSerializer)
from django.core.mail import send_mail
from .models import EmailOTP

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    s = UserRegistrationSerializer(data=request.data)
    if s.is_valid():
        user = s.save()
        user.is_active = False
        user.save()

        otp_code = EmailOTP.generate_otp()
        EmailOTP.objects.create(user=user, otp=otp_code)

        send_mail(
            subject='HackArena OTP Verification',
            message=f'Your OTP is: {otp_code}',
            from_email='yourgmail@gmail.com',
            recipient_list=[user.email],
        )

        return Response({
            "message": "OTP sent to email. Please verify.",
            "user_id": user.id
        }, status=201)

    return Response(s.errors, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    s = UserLoginSerializer(data=request.data)
    if s.is_valid():
        user = s.validated_data['user']
        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserProfileSerializer(user).data
        })
    return Response(s.errors, status=400)


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


@api_view(['GET'])
@permission_classes([AllowAny])
def user_detail(request, username):
    try:
        user = CTFUser.objects.get(username=username)
        return Response(PublicUserSerializer(user).data)
    except CTFUser.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)


@api_view(['GET'])
@permission_classes([AllowAny])
def user_list(request):
    users = CTFUser.objects.filter(is_banned=False)
    return Response(PublicUserSerializer(users, many=True).data)
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    user_id = request.data.get("user_id")
    otp = request.data.get("otp")

    try:
        user = CTFUser.objects.get(id=user_id)
        otp_record = EmailOTP.objects.filter(user=user, otp=otp, is_verified=False).latest('created_at')
    except:
        return Response({"error": "Invalid OTP"}, status=400)

    if otp_record.is_expired():
        return Response({"error": "OTP expired"}, status=400)

    otp_record.is_verified = True
    otp_record.save()

    user.is_active = True
    user.save()

    refresh = RefreshToken.for_user(user)

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "message": "Account verified successfully!"
    })