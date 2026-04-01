from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from .models import Challenge, Category, Hint, HintUnlock, Event
from .serializers import (ChallengeListSerializer, ChallengeDetailSerializer,
                           CategorySerializer, ChallengeAdminSerializer, EventSerializer)


@api_view(['GET'])
@permission_classes([AllowAny])
def challenge_list(request):
    qs = Challenge.objects.filter(is_active=True).select_related('category')
    if cat := request.query_params.get('category'):
        qs = qs.filter(category_id=cat)
    if diff := request.query_params.get('difficulty'):
        qs = qs.filter(difficulty=diff)
    return Response(ChallengeListSerializer(qs, many=True, context={'request': request}).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def challenge_detail(request, pk):
    try:
        c = Challenge.objects.get(pk=pk, is_active=True)
        return Response(ChallengeDetailSerializer(c, context={'request': request}).data)
    except Challenge.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)


@api_view(['GET'])
@permission_classes([AllowAny])
def category_list(request):
    return Response(CategorySerializer(Category.objects.all(), many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unlock_hint(request, hint_id):
    try:
        hint = Hint.objects.get(pk=hint_id)
    except Hint.DoesNotExist:
        return Response({'error': 'Hint not found'}, status=404)
    if HintUnlock.objects.filter(user=request.user, hint=hint).exists():
        return Response({'text': hint.text, 'already_unlocked': True})
    if hint.cost > 0 and request.user.get_score() < hint.cost:
        return Response({'error': f'Not enough points. Cost: {hint.cost}'}, status=400)
    HintUnlock.objects.create(user=request.user, hint=hint)
    return Response({'text': hint.text, 'cost': hint.cost})


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def admin_challenge_list(request):
    if request.method == 'GET':
        return Response(ChallengeAdminSerializer(Challenge.objects.all(), many=True).data)
    s = ChallengeAdminSerializer(data=request.data)
    if s.is_valid():
        s.save()
        return Response(s.data, status=201)
    return Response(s.errors, status=400)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAdminUser])
def admin_challenge_detail(request, pk):
    try:
        c = Challenge.objects.get(pk=pk)
    except Challenge.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)
    if request.method == 'GET':
        return Response(ChallengeAdminSerializer(c).data)
    if request.method == 'PUT':
        s = ChallengeAdminSerializer(c, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)
    c.delete()
    return Response(status=204)


@api_view(['GET'])
@permission_classes([AllowAny])
def event_detail(request):
    try:
        event = Event.objects.filter(is_active=True).first()
        if not event:
            return Response({'error': 'No active event found'}, status=404)
        return Response(EventSerializer(event).data)
    except Event.DoesNotExist:
        return Response({'error': 'Event not found'}, status=404)
