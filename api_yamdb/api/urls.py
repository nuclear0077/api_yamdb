from django.urls import include, path
from rest_framework import routers

from .views import (
    UserViewSet,
    confirmation_code,
    get_token,
    CategoryViewSet,
    GenreViewSet,
    TitleViewSet)

router_v1 = routers.DefaultRouter()
router_v1.register('users', UserViewSet, basename='users')
router_v1.register('categories', CategoryViewSet, basename='categories')
router_v1.register('genres', GenreViewSet, basename='genres')
router_v1.register('titles', TitleViewSet, basename='titles')

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