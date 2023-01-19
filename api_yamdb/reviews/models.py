from django.db import models

class Category(models.Model):
    name = models.CharField(
        max_length=256,
        verbose_name='Название категории',
        unique=True
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Имя группе в формате Slug'
    )

    def __str__(self):
        return f'Категория: {self.name}'

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Genre(models.Model):
    name = models.CharField(
        max_length=256,
        verbose_name='Название жанра',
        unique=True
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Имя жанра в формате Slug'
    )

    def __str__(self):
        return f'Жанр: {self.name}'

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


class Title(models.Model):
    name = models.CharField(
        max_length=256,
        verbose_name='Название категории',
        unique=True
    )
    year = models.PositiveSmallIntegerField(
        verbose_name='Год выпуска произведения'
    )
    category = models.ForeignKey(
        Category,
        related_name='titles',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='Категория произведения')
    genre = models.ManyToManyField(Genre, )

    def __str__(self):
        return f'Произведение: {self.name}'

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
