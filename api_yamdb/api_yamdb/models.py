from django.contrib.auth.models import AbstractUser
from django.db import models


class Roles(models.TextChoices):
    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'


class YamUser(AbstractUser):
    first_name = models.CharField(
        max_length=150,
        verbose_name='Firstname',
        null=True)
    last_name = models.CharField(
        max_length=150,
        verbose_name='Lastname',
        null=True)
    username = models.CharField(
        max_length=150,
        verbose_name='Username',
        unique=True
    )
    bio = models.TextField(null=True)
    email = models.EmailField(
        verbose_name='Email',
        unique=True,
        max_length=254
    )
    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.USER,

    )
    confirmation_code = models.CharField(max_length=100, blank=True, )

    @property
    def is_admin(self):
        return (
                self.role == Roles.ADMIN
                or self.is_superuser
                or self.is_staff
        )

    @property
    def is_moderator(self):
        return self.role == Roles.MODERATOR

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['email'],
                name='unique_email'),
        ]


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
