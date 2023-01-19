from django.urls import include, path
from rest_framework import routers

from .views import (
    UserViewSet,
    confirmation_code,
    get_token)

app_name = 'api_v1'
router_v1 = routers.DefaultRouter()
router_v1.register('users', UserViewSet, basename='users')

auth_urls = [
    path(
        'signup/', confirmation_code,
        name='generate_confirmation_code'),
    path(
        'token/', get_token,
        name='generate_token'),
]

urlpatterns = [
    path('v1/auth/', include(auth_urls)),
    path('v1/', include(router_v1.urls), name='users-v1'),
]