from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import User, UserRequest
from rest_framework.authtoken.models import Token
from django.db.models import Q


class SignUpSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password_1 = serializers.CharField(required=True, allow_null=False)
    password_2 = serializers.CharField(required=True, allow_null=False)
    first_name = serializers.CharField(required=True, allow_null=False)

    def save(self, **kwargs):
        password_1 = self.validated_data.get("password_1")
        password_2 = self.validated_data.get("password_2")
        if password_1 != password_2:
            raise serializers.ValidationError("your password did not match.")
        first_name = self.validated_data.get('first_name')
        user = User.objects.create_user(email=self.validated_data.get("email").lower(),
                                        password=password_1, first_name=first_name)
        token = Token.objects.get_or_create(user=user)[0]
        return token.key


def email_validation(value):
    if not User.objects.filter(email=value).exists():
        raise serializers.ValidationError("User not exists with given email.")
    return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, allow_null=False, allow_blank=False, validators=[email_validation])
    password = serializers.CharField(required=True, allow_null=False, allow_blank=False)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                                email=email, password=password)

            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "username" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data.get("user")
        token = Token.objects.get_or_create(user=user)[0]
        return token.key


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "email", "first_name"
        ]


class UserRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRequest
        fields = [
            "requestor", "requestee", "status", "id",
        ]
        extra_kwargs = {
            'requestor': {'required': False},
            'requestee': {'required': True, "allow_null": False},
            "status": {"read_only": True}
        }

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context["requestor"] = UserSerializer(instance=instance.requestor).data
        context["requestee"] = UserSerializer(instance=instance.requestee).data
        return context

    def create(self, validated_data):
        requestee = self.validated_data.get("requestee")
        user = self.context.get("user")
        if requestee == user:
            raise serializers.ValidationError("self assign can not work.")
        existing_request = UserRequest.objects.filter(
            Q(requestor=user, requestee=requestee, status=UserRequest.UserRequestStatus.pending) |
            Q(requestor=requestee, requestee=user, status=UserRequest.UserRequestStatus.pending),
        ).exists()
        if existing_request:
            raise serializers.ValidationError("Request already in pending stage.")
        if user.friends.filter(email=requestee.email).exists():
            raise serializers.ValidationError("You are already a friend.")
        validated_data["requestor"] = user
        return super().create(validated_data)
