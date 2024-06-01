import random
import string

from django.contrib.auth import get_user_model

from server.authentication.models import ConfirmationCode

UserModel = get_user_model()

def generate_confirmation_code(user_pk):
    code = ''.join(random.choices(string.digits, k=5))
    user = UserModel.objects.get(pk=user_pk)
    try:
        old_confirmation = ConfirmationCode.objects.get(user=user, type="AccountVerification")
        return old_confirmation
    except ConfirmationCode.DoesNotExist:
        code = ConfirmationCode.objects.create(user=user, code=code, type="AccountVerification")
        return code