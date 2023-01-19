from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from api_yamdb.api_yamdb.models import YamUser, Category, Genre, Title

admin.site.register(YamUser, UserAdmin)
@admin.register(Category)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'slug',
    )
    list_editable = ('name', 'slug', )
    search_fields = ('name',)
    list_filter = ('slug',)
    empty_value_display = '-пусто-'


@admin.register(Title)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'year',
        'category',
    )
    list_editable = ('name', 'year',)
    search_fields = ('name',)
    list_filter = ('category',)
    empty_value_display = '-пусто-'

admin.site.register(
    Genre
)
