from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CTFUser
import re


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    password_confirm = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = CTFUser
        fields = ['username', 'email', 'password', 'password_confirm', 'country']

    def validate_username(self, value):
        if not re.match(r'^[a-zA-Z0-9_]{3,30}$', value):
            raise serializers.ValidationError(
                "Username must be 3-30 characters, alphanumeric and underscores only."
            )
        return value

    def validate_email(self, value):
        if CTFUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_password(self, value):
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Password must contain at least one digit.")
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', value):
            raise serializers.ValidationError("Password must contain at least one special character.")
        return value

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return CTFUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
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
