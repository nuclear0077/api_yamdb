from django.contrib import admin

from .models import Category, Genre, Title, TitleGenre


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
admin.site.register(
    TitleGenre
)