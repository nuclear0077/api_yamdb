
import jwt
from api.permissions import IsAdminOrReadOnlyPermission, \
    IsAuthorAndStaffOrReadOnly
from api_yamdb.models import YamUser
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication, \
    BasicAuthentication
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import SearchFilter
from rest_framework.permissions import (AllowAny)
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from reviews.models import Category, Genre, Title, Review

from .serializers import (
    SendEmailSerializer,
    UserSerializer,
    CategorySerializer,
    GenreSerializer,
    TitleSerializer,
    TitleSerializerGet,
    ReviewSerializer,
    CommentSerializer)
from .utils import email_is_valid, email_msg, username_is_valid, is_auth, \
    is_admin_or_superuser, CreateListDestroyViewsSet, TitleFilter


@api_view(['POST'])
@permission_classes([AllowAny])
def get_token(request):
    username = request.data.get('username')
    serializer = SendEmailSerializer(data=request.data)
    serializer.is_valid(raise_exception=False)
    if username is None:
        return Response(serializer.data, status.HTTP_400_BAD_REQUEST)

    user = get_object_or_404(YamUser, username=username)

    if user.confirmation_code == request.data.get('confirmation_code'):
        return Response(
            {'token': str(AccessToken.for_user(user))},
            status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def confirmation_code(request):
    email = request.data.get('email')
    username = request.data.get('username')
    serializer = SendEmailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if email is None \
            or username is None \
            or username == 'me' \
            or not email_is_valid(email) \
            or not username_is_valid(username):
        return Response(serializer.data, status.HTTP_400_BAD_REQUEST)
    else:
        user = YamUser.objects.filter(email=email).exclude(username=username)
        if user.exists():
            return Response(serializer.data, status.HTTP_400_BAD_REQUEST)

        user = YamUser.objects.filter(username=username).exclude(email=email)
        if user.exists():
            return Response(serializer.data, status.HTTP_400_BAD_REQUEST)

        user = YamUser.objects.filter(email=email, username=username)
        if user.exists():
            return Response(serializer.data, status.HTTP_200_OK)
        else:
            user = YamUser.objects.create(email=email, username=username)
            confirmation = default_token_generator.make_token(user)
            email_msg(email, confirmation)
            user.confirmation_code = confirmation
            user.save()
            return Response(serializer.data, status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    queryset = YamUser.objects.all()
    serializer_class = UserSerializer
    lookup_field = "username"
    filter_backends = (SearchFilter,)
    search_fields = ['username']
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    pagination_class = PageNumberPagination

    def list(self, request, *args, **kwargs):
        if not is_auth(request):
            return Response(request.data, status.HTTP_401_UNAUTHORIZED)

        user = get_user_by_token(request)
        if not is_admin_or_superuser(user):
            serializer = UserSerializer(instance=user)
            return Response(serializer.data, status.HTTP_403_FORBIDDEN)

        page = self.paginate_queryset(self.filter_queryset(self.queryset))
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(self.queryset, many=True)
            response_data = serializer.data

        return response_data

    def retrieve(self, request, *args, **kwargs):
        if not is_auth(request):
            return Response(request.data, status.HTTP_401_UNAUTHORIZED)

        user = get_user_by_token(request)
        serializer = UserSerializer(instance=user)

        if "me" == kwargs.get('username'):
            return Response(serializer.data, status=status.HTTP_200_OK)

        if not is_admin_or_superuser(user):
            return Response(serializer.data, status.HTTP_403_FORBIDDEN)

        user = YamUser.objects.filter(
            username=self.kwargs.get('username')).first()
        return Response(UserSerializer(
            instance=user).data,
            status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        user = get_user_by_token(request)

        if "me" == kwargs.get('username'):
            if not username_is_valid(request.data.get('username')):
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(user,
                                             data=request.data,
                                             partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(role=user.role)
            return Response(status=status.HTTP_200_OK)

        if not is_admin_or_superuser(user):
            return Response(request.data, status.HTTP_403_FORBIDDEN)
        else:
            update_user = YamUser.objects.filter(
                username=self.kwargs.get('username')).first()
            serializer = self.get_serializer(update_user,
                                             data=request.data,
                                             partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        return Response(request.data, status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        if "/me" in str(request.get_full_path()):
            return Response(request.data, status.HTTP_405_METHOD_NOT_ALLOWED)

        if not is_admin_or_superuser(get_user_by_token(request)):
            return Response(request.data, status.HTTP_403_FORBIDDEN)
        else:
            self.perform_destroy(self.get_object())
            return Response(request.data, status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        username = request.data.get('username')
        user = YamUser.objects.filter(email=email, username=username)
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not username_is_valid(username):
            return Response(request.data,
                            status=status.HTTP_400_BAD_REQUEST)
        if not user.exists():
            user = YamUser.objects.create(email=email, username=username)
            user.save()
            return Response(request.data, status=status.HTTP_201_CREATED)


def get_user_by_token(request):
    token = request.META.get('HTTP_AUTHORIZATION', None)
    token = token.replace("Bearer ", "")
    user_json = jwt.decode(token, options={"verify_signature": False})
    return YamUser.objects.get(id=user_json['user_id'])


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
        queryset = self.filter_queryset(Title.objects.all())
        serializer = TitleSerializerGet(queryset, many=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Title.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = TitleSerializerGet(user)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthorAndStaffOrReadOnly, ]

    def get_queryset(self):
        title = get_object_or_404(
            Title,
            id=self.kwargs.get('title_id'))
        return title.reviews.all()

    def perform_create(self, serializer):
        title = get_object_or_404(
            Title,
            id=self.kwargs.get('title_id'))
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthorAndStaffOrReadOnly, ]

    def get_queryset(self):
        review = get_object_or_404(
            Review,
            id=self.kwargs.get('review_id'))
        return review.comments.all()

    def perform_create(self, serializer):
        review = get_object_or_404(
            Review,
            id=self.kwargs.get('review_id'))
        serializer.save(author=self.request.user, review=review)
