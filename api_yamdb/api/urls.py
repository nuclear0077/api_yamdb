from django.urls import include, path
from rest_framework import routers

from .views import (TokenObtainView, SendEmailView, UserViewSet,
    confirmation_code)
router_v1 = routers.DefaultRouter()
router_v1.register('users/', UserViewSet, basename='User')

auth_urls = [
    path(
        'signup/', confirmation_code,
        name='generate_confirmation_code'),
    path(
        'token/', TokenObtainView.as_view(),
        name='generate_token'),
]

urlpatterns = [
    path('api/v1/auth/', include(auth_urls)),
    path('api/v1/', include(router_v1.urls), name='users-v1'),
]
