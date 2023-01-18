from api_yamdb.models import YamUser
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator as token,\
    default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import (AllowAny, IsAuthenticated)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import IsAdmin
from .serializers import (
    TokenSerializer,
    SendEmailSerializer,
    UserSerializer)
from .utils import email_is_valid, email_msg, username_is_valid


class TokenObtainView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(
            raise_exception=True)
        user, created = YamUser.objects.get_or_create(
            email=request.data['email'])
        if not token.check_token(user, request.data['confirmation code']):
            raise AuthenticationFailed()
        refresh = RefreshToken.for_user(user)
        return Response('token: ' + str(refresh.access_token),
            status=status.HTTP_200_OK)


class SendEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = self.request.data['email']
        user = get_object_or_404(YamUser, email=email)
        confirmation_code = token.make_token(user)
        send_mail(
            'Confirmation code email',
            'confirmation code: {}'.format(confirmation_code),
            settings.DOMAIN_NAME,
            [email],
            fail_silently=False,
        )
        return Response(
            f'Code was sent on email {email}',
            status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def confirmation_code(request):
    email = request.data.get('email')
    username = request.data.get('username')
    serializer = SendEmailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if email is None or username is None or not email_is_valid(email) or not \
            username_is_valid(
            username):
        return Response(serializer.data, status.HTTP_400_BAD_REQUEST)
    else:
        user = YamUser.objects.create(email=email, username=username)
        confirmation = default_token_generator.make_token(user)
        email_msg(email, confirmation)
        user.confirmation_code = confirmation
        message = email
        user.save()
    return Response(serializer.data, status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    queryset = YamUser.objects.all()
    serializer_class = UserSerializer
    lookup_field = "username"
    permission_classes = [IsAuthenticated, IsAdmin]
    search_fields = ['username', ]

    @action(
        detail=False,
        methods=['get', 'patch'],
        permission_classes=[IsAuthenticated],
        url_name='me', url_path='me')
    def me(self, request):
        if self.request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(role=request.user.role)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK)
