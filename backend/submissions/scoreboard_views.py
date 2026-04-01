from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from users.models import CTFUser
from teams.models import Team
from .models import Submission


@api_view(['GET'])
@permission_classes([AllowAny])
def user_scoreboard(request):
    users = CTFUser.objects.filter(is_banned=False, is_staff=False)
    board = []
    for u in users:
        score = u.get_score()
        if score > 0:
            last = Submission.objects.filter(user=u, is_correct=True).order_by('-submitted_at').first()
            board.append({
                'rank': 0, 'user_id': u.id, 'username': u.username,
                'country': u.country, 'score': score,
                'solved_count': u.get_solved_count(),
                'last_solve': last.submitted_at if last else None,
                'team': u.team.name if u.team else None,
            })
    board.sort(key=lambda x: (-x['score'], str(x['last_solve'] or '9999')))
    for i, e in enumerate(board):
        e['rank'] = i + 1
    return Response(board)


@api_view(['GET'])
@permission_classes([AllowAny])
def team_scoreboard(request):
    board = []
    for t in Team.objects.filter(is_hidden=False):
        score = t.get_score()
        if score > 0:
            board.append({
                'rank': 0, 'team_id': t.id, 'team_name': t.name,
                'score': score, 'member_count': t.get_member_count(),
            })
    board.sort(key=lambda x: -x['score'])
    for i, e in enumerate(board):
        e['rank'] = i + 1
    return Response(board)


@api_view(['GET'])
@permission_classes([AllowAny])
def score_over_time(request):
    top_n = int(request.query_params.get('top', 10))
    users = sorted(
        [u for u in CTFUser.objects.filter(is_banned=False, is_staff=False)],
        key=lambda u: -u.get_score()
    )[:top_n]
    result = []
    for user in users:
        if user.get_score() == 0:
            continue
        solves = Submission.objects.filter(user=user, is_correct=True).select_related('challenge').order_by('submitted_at')
        cum = 0
        timeline = []
        for s in solves:
            cum += s.challenge.get_current_points()
            timeline.append({'time': s.submitted_at, 'score': cum, 'challenge': s.challenge.title})
        result.append({'username': user.username, 'timeline': timeline})
    return Response(result)
