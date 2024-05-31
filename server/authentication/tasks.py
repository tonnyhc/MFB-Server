import random
import string

from celery import Celery, shared_task
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

from server import settings
from server.authentication.models import ConfirmationCode
from server.cloudinary import upload_to_cloudinary
from server.profiles.models import Profile

UserModel = get_user_model()

app = Celery('tasks', broker='redis://localhost:6379/0')


@shared_task
def send_confirmation_code_for_register(user_pk):
    user = UserModel.objects.get(pk=user_pk)
    code = ''.join(random.choices(string.digits, k=5))
    try:
        old_confirmation = ConfirmationCode.objects.get(user=user, type="AccountVerification")
        code = old_confirmation.code
    except ConfirmationCode.DoesNotExist:
        ConfirmationCode.objects.create(user=user, code=code, type="AccountVerification")

    subject = 'Confirm your email address!'
    message = f"Your confirmation code is: {code}"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list)


@shared_task
def send_confirmation_code_forgotten_password(user_pk):
    code = ''.join(random.choices(string.digits, k=5))
    user = UserModel.objects.get(pk=user_pk)
    try:
        old_confirmation = ConfirmationCode.objects.get(user=user, type="ForgottenPassword")
        code = old_confirmation.code
    except ConfirmationCode.DoesNotExist:
        code = ConfirmationCode.objects.create(user=user, code=code, type="ForgottenPassword"),

    subject = "Reset your password!"
    message = f"Your verification code is: {code}"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list)
    return True


@shared_task
def upload_profile_picture_to_cloudinary_and_save_to_profile(image_url, profile_id):
    try:
        # Upload the image to Cloudinary
        public_id = upload_to_cloudinary(image_url)

        # Update the profile with the Cloudinary public ID
        profile = Profile.objects.get(pk=profile_id)
        profile.picture = public_id
        profile.save()
    except Profile.DoesNotExist:
        # Handle the case where the profile object is not found
        # Log the error or take appropriate action
        pass
