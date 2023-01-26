from django.contrib.auth.models import AbstractUser
from django.db import models


class Roles(models.TextChoices):
    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'


class User(AbstractUser):
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
    confirmation_code = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        editable=False,
        unique=True)

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

    @property
    def is_user(self):
        return self.role == Roles.USER

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'], name='unique_username_email'
            )
        ]
