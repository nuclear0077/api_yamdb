from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from django.utils import timezone

from reviews.models import Category, Genre, Title, Review, Comment
from core.utils import username_is_valid

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            'first_name',
            'last_name',
            'email',
            'username',
            'bio',
            'role']
        model = User

    def validate(self, data):
        if not username_is_valid(data.get('username')):
            raise serializers.ValidationError(
                "Unexpected pattern"
            )
        return data


class SendEmailSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=254, required=True)
    username = serializers.CharField(max_length=150, required=True)

    class Meta:
        fields = ('email', 'username')
        model = User

    def validate(self, data):
        if data['username'] == 'me':
            raise serializers.ValidationError(
                "Me is not allowed"
            )
        if not username_is_valid(data.get('username')):
            raise serializers.ValidationError(
                "Unexpected pattern"
            )
        user = User.objects.filter(username=data.get('username'))
        email = User.objects.filter(email=data.get('email'))
        if not user.exists() and email.exists():
            raise ValidationError("Недопустимый email")
        if user.exists() and user.get().email != data.get('email'):
            raise ValidationError("Недопустимый email")

        return data


class TokenSerializer(serializers.ModelSerializer):
    username = serializers.CharField()
    confirmation_code = serializers.CharField()

    class Meta:
        model = User
        fields = ('username', 'confirmation_code',)


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
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(read_only=True, many=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        fields = ('id', 'name', 'year',
                  'description', 'genre', 'category', 'rating')
        model = Title


class TitleSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=256)
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
        if value > timezone.now().year:
            raise serializers.ValidationError(" год выпуска не может быть"
                                              "больше текущего")
        return value


class ReviewSerializer(serializers.ModelSerializer):
    title = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True
    )
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        fields = ('id', 'title', 'text', 'author', 'score', 'pub_date')
        model = Review

    def validate(self, data):
        request = self.context['request']
        author = request.user
        title_id = self.context.get('view').kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        if (
                request.method == 'POST'
                and Review.objects.filter(title=title, author=author).exists()
        ):
            raise ValidationError('Вы уже оставили отзыв на это произведение')
        return data


class CommentSerializer(serializers.ModelSerializer):
    review = serializers.SlugRelatedField(
        slug_field='text',
        read_only=True
    )
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        fields = ('id', 'text', 'author', 'pub_date', 'review')
        model = Comment
