import random
import string
import logging

from celery import Celery, shared_task
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from server import settings
from server.authentication.models import ConfirmationCode
from server.cloudinary import upload_to_cloudinary
from server.profiles.models import Profile

logger = logging.getLogger('server')
UserModel = get_user_model()

app = Celery('tasks', broker='redis://localhost:6379/0')


@shared_task
def send_confirmation_code_for_register(code_pk, user_pk):
    code_instance = ConfirmationCode.objects.get(pk=code_pk)
    code = code_instance.code
    user = UserModel.objects.get(pk=user_pk)
    subject = 'Confirm your email address!'
    html_message = render_to_string('account_verification_template.html', {'activation_code': code})
    plain_message = strip_tags(html_message)
    from_email = settings.EMAIL_HOST_USER

    recipient_list = [user.email]
    try:
        send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)
        print('Confirmation email sent successfully!')
    except Exception as e:
        print(f'Failed to send confirmation email: {e}')


@shared_task
def send_confirmation_code_forgotten_password(user_pk):
    code = ''.join(random.choices(string.digits, k=5))
    user = UserModel.objects.get(pk=user_pk)
    try:
        old_confirmation = ConfirmationCode.objects.get(user=user, type="ForgottenPassword")
        code = old_confirmation.code
    except ConfirmationCode.DoesNotExist:
        code_instance = ConfirmationCode.objects.create(user=user, code=code, type="ForgottenPassword")
        code = code_instance.code
    subject = "Reset your password!"
    html_message = render_to_string('forgotten_password_template.html', {'reset_code': code})
    plain_message = strip_tags(html_message)
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user.email]
    send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)

    return True


