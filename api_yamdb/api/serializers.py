from abc import ABC

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=254,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        max_length=150,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        fields = [
            'first_name',
            'last_name',
            'email',
            'username',
            'bio',
            'role']
        model = User


class TokenSerializer(serializers.Serializer):
    username_field = get_user_model().USERNAME_FIELD

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['confirmation code'] = serializers.CharField()
        self.fields[self.username_field] = serializers.EmailField()


class SendEmailSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=254)
    username = serializers.CharField(max_length=150)
    extra_kwargs = {
        'email': {'required': True},
        'username': {'read_only': True}
    }

    class Meta:
        fields = ('email', 'username')
        model = User
