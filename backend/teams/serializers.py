from rest_framework import serializers
from .models import Team


class TeamMemberSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    country = serializers.CharField()
    score = serializers.SerializerMethodField()
    solved_count = serializers.SerializerMethodField()

    def get_score(self, obj): return obj.get_score()
    def get_solved_count(self, obj): return obj.get_solved_count()


class TeamSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    captain_username = serializers.CharField(source='captain.username', read_only=True)

    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'captain_username',
                  'members', 'score', 'member_count', 'max_members', 'created_at']

    def get_members(self, obj):
        return TeamMemberSerializer(obj.members, many=True).data

    def get_score(self, obj): return obj.get_score()
    def get_member_count(self, obj): return obj.get_member_count()


class TeamCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['name', 'description', 'max_members']


class TeamPublicSerializer(serializers.ModelSerializer):
    score = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ['id', 'name', 'score', 'member_count', 'created_at']

    def get_score(self, obj): return obj.get_score()
    def get_member_count(self, obj): return obj.get_member_count()
