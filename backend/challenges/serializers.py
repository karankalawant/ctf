from rest_framework import serializers
from .models import Challenge, Category, Hint, HintUnlock, Event


class CategorySerializer(serializers.ModelSerializer):
    challenge_count = serializers.SerializerMethodField()
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'color', 'challenge_count']
    def get_challenge_count(self, obj):
        return obj.challenges.filter(is_active=True).count()


class HintSerializer(serializers.ModelSerializer):
    is_unlocked = serializers.SerializerMethodField()
    text_masked = serializers.SerializerMethodField()
    class Meta:
        model = Hint
        fields = ['id', 'cost', 'order', 'is_unlocked', 'text_masked']

    def get_is_unlocked(self, obj):
        req = self.context.get('request')
        if not req or not req.user.is_authenticated: return False
        return HintUnlock.objects.filter(user=req.user, hint=obj).exists()

    def get_text_masked(self, obj):
        req = self.context.get('request')
        if req and req.user.is_authenticated:
            if HintUnlock.objects.filter(user=req.user, hint=obj).exists():
                return obj.text
        return None


class ChallengeListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    solve_count = serializers.SerializerMethodField()
    current_points = serializers.SerializerMethodField()
    is_solved = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = ['id', 'title', 'category_name', 'category_color',
                  'difficulty', 'points', 'current_points', 'solve_count',
                  'is_solved', 'is_active', 'author']

    def get_solve_count(self, obj): return obj.get_solve_count()
    def get_current_points(self, obj): return obj.get_current_points()
    def get_is_solved(self, obj):
        req = self.context.get('request')
        if not req or not req.user.is_authenticated: return False
        from submissions.models import Submission
        return Submission.objects.filter(user=req.user, challenge=obj, is_correct=True).exists()


class ChallengeDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    solve_count = serializers.SerializerMethodField()
    current_points = serializers.SerializerMethodField()
    is_solved = serializers.SerializerMethodField()
    hints = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = ['id', 'title', 'description', 'category', 'difficulty',
                  'points', 'current_points', 'files', 'url',
                  'solve_count', 'is_solved', 'hints', 'author', 'created_at']

    def get_solve_count(self, obj): return obj.get_solve_count()
    def get_current_points(self, obj): return obj.get_current_points()
    def get_is_solved(self, obj):
        req = self.context.get('request')
        if not req or not req.user.is_authenticated: return False
        from submissions.models import Submission
        return Submission.objects.filter(user=req.user, challenge=obj, is_correct=True).exists()
    def get_hints(self, obj):
        return HintSerializer(obj.hint_objects.all(), many=True, context=self.context).data


class ChallengeAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = '__all__'


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'name', 'start_date', 'end_date', 'is_active']
