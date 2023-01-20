import uuid

import jwt
from api_yamdb.models import YamUser, Category, Genre, Title
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication,\
    BasicAuthentication
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (AllowAny)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from .utils import CreateListDestroyViewsSet

from .serializers import (
    SendEmailSerializer,
    UserSerializer,
    CategorySerializer,
    GenreSerializer,
    TitleSerializer)
from .utils import email_is_valid, email_msg, username_is_valid, is_auth,\
    is_admin_or_superuser


@api_view(['POST'])
@permission_classes([AllowAny])
def get_token(request):
    username = request.data.get('username')
    serializer = SendEmailSerializer(data=request.data)
    serializer.is_valid(raise_exception=False)
    if username is None:
        return Response(serializer.data, status.HTTP_400_BAD_REQUEST)

    user = get_object_or_404(YamUser, username=username)

    if (str(uuid.uuid3(uuid.NAMESPACE_DNS, user.email)) ==
            request.data.get('confirmation_code')):
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
    if email is None\
            or username is None\
            or username == 'me'\
            or not email_is_valid(email)\
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
    lookup_field = 'slug'


class GenreViewSet(CreateListDestroyViewsSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    lookup_field = 'slug'


class TitleViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    queryset = Title.objects.all()
    serializer_class = TitleSerializer
