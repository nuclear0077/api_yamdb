from django.core import mail
from django.core.exceptions import ValidationError
from django.core.validators import validate_email, RegexValidator
from django.utils.regex_helper import _lazy_re_compile


def email_is_valid(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


username_validator = RegexValidator(
    _lazy_re_compile(r'^[\w.@+-]+\Z'),
    message='Enter a valid username.',
    code='invalid',
)


def username_is_valid(username):
    try:
        username_validator(username)
        return True
    except ValidationError:
        return False


def email_msg(to_email, code):
    subject = 'Confirmation code for YaMDB'
    to = to_email
    text_content = f'''Confirmation codefor API YaMDB. {code}'''
    mail.send_mail(
        subject, text_content,
        'noreply@yamdb.ru', [to],
        fail_silently=False
    )
