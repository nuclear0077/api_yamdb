from rest_framework import mixins
from rest_framework import viewsets

from django.core.validators import validate_email
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.regex_helper import _lazy_re_compile
from django.conf import settings


username_validator = RegexValidator(
    _lazy_re_compile(r'^[\w.@+-]+\Z'),
    message='Enter a valid username.',
    code='invalid',
)


def email_is_valid(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def username_is_valid(username):
    try:
        username_validator(username)
        return True
    except ValidationError:
        return False


def email_msg(to_email, code):
    subject = 'Confirmation code for YaMDB'
    to = to_email
    text_content = f'Confirmation code for API YaMDB. {code}'
    mail.send_mail(
        subject, text_content,
        settings.EMAIL_NO_REPLY, [to],
        fail_silently=False
    )


class CreateListDestroyViewsSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    pass
