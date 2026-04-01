from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CTFUser


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = CTFUser
        fields = ['username', 'email', 'password', 'password_confirm', 'country']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return CTFUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            country=validated_data.get('country', ''),
        )


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.is_active:
            raise serializers.ValidationError("Account not verified.")
        if user.is_banned:
            raise serializers.ValidationError("Account is banned.")
        data['user'] = user
        return data
        


class UserProfileSerializer(serializers.ModelSerializer):
    score = serializers.SerializerMethodField()
    solved_count = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()

    class Meta:
        model = CTFUser
        fields = ['id', 'username', 'email', 'bio', 'country', 'avatar_url',
                  'team_name', 'score', 'solved_count', 'is_staff', 'created_at']
        read_only_fields = ['id', 'username', 'is_staff', 'created_at']

    def get_score(self, obj): return obj.get_score()
    def get_solved_count(self, obj): return obj.get_solved_count()
    def get_team_name(self, obj):
        t = obj.team
        return t.name if t else None


class PublicUserSerializer(serializers.ModelSerializer):
    score = serializers.SerializerMethodField()
    solved_count = serializers.SerializerMethodField()

    class Meta:
        model = CTFUser
        fields = ['id', 'username', 'country', 'score', 'solved_count']

    def get_score(self, obj): return obj.get_score()
    def get_solved_count(self, obj): return obj.get_solved_count()
