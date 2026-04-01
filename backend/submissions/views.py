from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import timedelta
from django.utils import timezone
from .models import Submission
from challenges.models import Challenge


def get_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_flag(request, challenge_id):
    try:
        challenge = Challenge.objects.get(pk=challenge_id, is_active=True)
    except Challenge.DoesNotExist:
        return Response({'error': 'Challenge not found'}, status=404)

    flag = request.data.get('flag', '').strip()
    if not flag:
        return Response({'error': 'Flag required'}, status=400)

    if Submission.objects.filter(user=request.user, challenge=challenge, is_correct=True).exists():
        return Response({'correct': False, 'message': 'Already solved!'})

    # Rate limit: 10 attempts per 5 minutes
    recent = Submission.objects.filter(
        user=request.user, challenge=challenge,
        submitted_at__gte=timezone.now() - timedelta(minutes=5)
    ).count()
    if recent >= 10:
        return Response({'error': 'Too many attempts. Wait 5 minutes.'}, status=429)

    is_correct = challenge.check_flag(flag)
    Submission.objects.create(
        user=request.user, challenge=challenge,
        flag=flag, is_correct=is_correct, ip_address=get_ip(request)
    )

    if is_correct:
        first_blood = challenge.get_solve_count() == 1
        return Response({
            'correct': True,
            'message': '🎉 Correct! Challenge solved!',
            'points': challenge.get_current_points(),
            'first_blood': first_blood,
        })
    return Response({'correct': False, 'message': '❌ Wrong flag. Try again!'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_submissions(request):
    subs = Submission.objects.filter(user=request.user).select_related('challenge')
    return Response([{
        'id': s.id,
        'challenge_id': s.challenge.id,
        'challenge_title': s.challenge.title,
        'is_correct': s.is_correct,
        'submitted_at': s.submitted_at,
    } for s in subs])
