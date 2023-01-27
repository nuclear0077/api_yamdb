from django.db.models import Avg
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.response import Response

from .filters import TitleFilter
from .permissions import (
    IsAdminOrReadOnlyPermission,
    IsAuthorAndStaffOrReadOnly, IsAdminUser,
)
from reviews.models import Category, Genre, Title, Review
from .serializers import (
    SendEmailSerializer,
    UserSerializer,
    CategorySerializer,
    GenreSerializer,
    TitleSerializer,
    TitleSerializerGet,
    ReviewSerializer,
    CommentSerializer,
    TokenSerializer)

from core.utils import (CreateListDestroyViewsSet, email_msg)

from reviews.models import User


@api_view(['POST'])
@permission_classes([AllowAny])
def get_token(request):
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_object_or_404(
        User,
        username=serializer.validated_data.get('username')
    )
    if (user.confirmation_code == serializer.validated_data.get(
            'confirmation_code')):
        return Response(
            {'token': str(AccessToken.for_user(user))},
            status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def confirmation_code(request):
    serializer = SendEmailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data.get('username')
    email = serializer.validated_data.get('email')
    user, created = User.objects.get_or_create(username=username, email=email)
    confirmation = default_token_generator.make_token(user)
    user.confirmation_code = confirmation
    user.save()
    email_msg(email, confirmation)
    return Response(data=serializer.data, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    queryset = User.objects.all()
    permission_classes = (IsAdminUser,)
    serializer_class = UserSerializer
    lookup_field = 'username'
    filter_backends = (SearchFilter,)
    search_fields = ['username']

    @action(
        detail=False,
        methods=(['GET', 'PATCH']),
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        if request.method == 'GET':
            serializer = UserSerializer(request.user)
            return Response(serializer.data)

        serializer = UserSerializer(
            request.user, data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(role=request.user.role)
        return Response(serializer.data)


class CategoryViewSet(CreateListDestroyViewsSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminOrReadOnlyPermission,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)
    lookup_field = 'slug'


class GenreViewSet(CreateListDestroyViewsSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminOrReadOnlyPermission,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)
    lookup_field = 'slug'


class TitleViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    queryset = Title.objects.all()
    permission_classes = (IsAdminOrReadOnlyPermission,)
    serializer_class = TitleSerializer
    filterset_class = TitleFilter
    filter_backends = (DjangoFilterBackend,)

    def list(self, request):
        queryset = self.filter_queryset(Title.objects.annotate(
            rating=Avg('reviews__score')))
        serializer = TitleSerializerGet(queryset, many=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Title.objects.annotate(rating=Avg('reviews__score'))
        user = get_object_or_404(queryset, pk=pk)
        serializer = TitleSerializerGet(user)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthorAndStaffOrReadOnly, ]

    def get_title(self):
        return get_object_or_404(Title, id=self.kwargs.get('title_id'))

    def get_queryset(self):
        return Review.objects.filter(title=self.get_title().id)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, title=self.get_title())


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthorAndStaffOrReadOnly, ]

    def get_queryset(self):
        review = get_object_or_404(
            Review,
            id=self.kwargs.get('review_id'),
            title__id=self.kwargs.get("title_id"))
        return review.comments.all()

    def perform_create(self, serializer):
        review = get_object_or_404(
            Review,
            id=self.kwargs.get('review_id'))
        serializer.save(author=self.request.user, review=review)
