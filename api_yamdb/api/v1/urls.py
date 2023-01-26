from django.urls import include, path
from rest_framework import routers

from .views import (
    UserViewSet,
    confirmation_code,
    get_token,
    CategoryViewSet,
    GenreViewSet,
    TitleViewSet,
    ReviewViewSet,
    CommentViewSet)

router_v1 = routers.DefaultRouter()
router_v1.register('users', UserViewSet, basename='users')
router_v1.register('categories', CategoryViewSet, basename='categories')
router_v1.register('genres', GenreViewSet, basename='genres')
router_v1.register('titles', TitleViewSet, basename='titles')
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews',
    ReviewViewSet,
    basename='reviews'
)
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet,
    basename='comments'
)

auth_urls = [
    path(
        'signup/', confirmation_code,
        name='generate_confirmation_code'),
    path(
        'token/', get_token,
        name='generate_token'),
]

urlpatterns = [
    path('auth/', include(auth_urls)),
    path('', include(router_v1.urls), name='users-v1'),
]
