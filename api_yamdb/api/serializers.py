from api_yamdb.models import YamUser
from reviews.models import Category, Genre, Title
from django.contrib.auth import get_user_model
import datetime
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=254,
        validators=[UniqueValidator(queryset=User.objects.all())])
    username = serializers.CharField(
        max_length=150,
        validators=[UniqueValidator(queryset=User.objects.all())])

    class Meta:
        fields = [
            'first_name',
            'last_name',
            'email',
            'username',
            'bio',
            'role']
        model = YamUser


class SendEmailSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=254)
    username = serializers.CharField(max_length=150)
    extra_kwargs = {
        'email': {'required': True},
        'username': {'read_only': True}
    }

    class Meta:
        fields = ('email', 'username')
        model = YamUser


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('name', 'slug')
        model = Category
        lookup_field = 'slug'


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('name', 'slug')
        model = Genre
        lookup_field = 'slug'


class TitleSerializerGet(serializers.ModelSerializer):
    category = CategorySerializer()
    genre = GenreSerializer(read_only=True, many=True)

    class Meta:
        fields = ('id', 'name', 'year', 'description', 'genre', 'category')
        model = Title


class TitleSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug')
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        many=True,
        slug_field='slug')

    class Meta:
        fields = ('id', 'name', 'year', 'description', 'genre', 'category')
        model = Title

    def validate_year(self, value):
        if value > datetime.datetime.now().year:
            raise serializers.ValidationError(" год выпуска не может быть"
                                              "больше текущего")
        return value
