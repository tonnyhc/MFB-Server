import random
import string

from django.core.mail import send_mail

from server import settings
from server.authentication.models import ConfirmationCode


def send_confirmation_code_for_register(instance):
    # Generate a 5 digit code
    # if created:
    code = ''.join(random.choices(string.digits, k=5))

    # Save the code to the db
    ConfirmationCode.objects.create(user=instance, code=code, type="AccountVerification")

    subject = 'Confirm your email address!'
    message = f"Your confirmation code is: {code}"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [instance.email]
    send_mail(subject, message, from_email, recipient_list)


def send_confirmation_code_forgotten_password(instance):
    code = ''.join(random.choices(string.digits, k=5))
    ConfirmationCode.objects.create(user=instance, code=code, type="ForgottenPassword"),

    subject = "Reset your password!"
    message = f"Your verification code is: {code}"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [instance.email]
    send_mail(subject, message, from_email, recipient_list)
