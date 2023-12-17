import random
import string

from django.core.mail import send_mail

from server import settings
from server.authentication.models import ConfirmationCode


def send_confirmation_code(instance):
    # Generate a 5 digit code
    # if created:
    code = ''.join(random.choices(string.digits, k=5))

    # Save the code to the db
    ConfirmationCode.objects.create(user=instance, code=code)

    subject = 'Confirm your email address!'
    message = f"Your confirmation code is: {code}"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [instance.email]
    send_mail(subject, message, from_email, recipient_list)
