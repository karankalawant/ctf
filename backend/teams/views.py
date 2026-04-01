from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import Team
from .serializers import TeamSerializer, TeamCreateSerializer, TeamPublicSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def team_list(request):
    return Response(TeamPublicSerializer(Team.objects.filter(is_hidden=False), many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def team_create(request):
    if request.user.team_id_ref:
        return Response({'error': 'Leave your current team first.'}, status=400)
    s = TeamCreateSerializer(data=request.data)
    if s.is_valid():
        team = s.save(captain=request.user)
        request.user.team_id_ref = team.pk
        request.user.save()
        return Response(TeamSerializer(team).data, status=201)
    return Response(s.errors, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def team_detail(request, pk):
    try:
        return Response(TeamSerializer(Team.objects.get(pk=pk)).data)
    except Team.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def team_join(request):
    code = request.data.get('invite_code')
    if not code:
        return Response({'error': 'Invite code required'}, status=400)
    if request.user.team_id_ref:
        return Response({'error': 'Leave your current team first.'}, status=400)
    try:
        team = Team.objects.get(invite_code=code)
    except Team.DoesNotExist:
        return Response({'error': 'Invalid invite code'}, status=400)
    if team.get_member_count() >= team.max_members:
        return Response({'error': 'Team is full'}, status=400)
    request.user.team_id_ref = team.pk
    request.user.save()
    return Response({'message': f'Joined {team.name}!', 'team': TeamSerializer(team).data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def team_leave(request):
    if not request.user.team_id_ref:
        return Response({'error': 'Not in a team'}, status=400)
    team = request.user.team
    team_name = team.name
    request.user.team_id_ref = None
    request.user.save()
    if team.captain_id == request.user.pk:
        remaining = team.members.exclude(pk=request.user.pk).first()
        if remaining:
            team.captain = remaining
            team.save()
        else:
            team.delete()
            return Response({'message': 'Left and disbanded team.'})
    return Response({'message': f'Left {team_name}.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_team(request):
    if not request.user.team_id_ref:
        return Response({'team': None})
    team = request.user.team
    if not team:
        return Response({'team': None})
    data = TeamSerializer(team).data
    data['invite_code'] = team.invite_code if team.captain_id == request.user.pk else None
    return Response({'team': data})
