from enum import Enum

from django.contrib.auth import get_user_model
from django.db import models, IntegrityError

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from rest_framework.exceptions import ValidationError
from simple_history.models import HistoricalRecords

from server.mixins import ChoicesEnumMixin
from server.models_utils import MAX_LEN_ACCOUNT_USERNAME


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)

        try:
            user.save(using=self._db)
        except IntegrityError:
            raise ValidationError('A user with this username/email already exists')
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

    @staticmethod
    def confirm_email(user, code):
        if not user:
            return False

        try:
            confirmation = user.confirmationcode_set.filter(type="AccountVerification").first()
        except ConfirmationCode.DoesNotExist:
            return False

        if confirmation.code != code:
            return False

        user.is_verified = True
        user.save()
        user.confirmationcode_set.filter(type="AccountVerification").delete()
        # confirmation.delete()
        return True


class AppUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, error_messages={
        'unique': "A user with this email already exists. "
    })
    username = models.CharField(
        max_length=MAX_LEN_ACCOUNT_USERNAME,
        unique=True,
        error_messages={
            'unique': "A user with this username already exists. "
        }
    )
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        related_name='appuser_set',  # add related_name argument
        help_text=
        'The groups this user belongs to. A user will get all permissions '
        'granted to each of their groups.',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        related_name='appuser_set',  # add related_name argument
        help_text='Specific permissions for this user.',
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


UserModel = get_user_model()

class ConfirmationCodeTypeChoices(ChoicesEnumMixin, Enum):
    AccountVerification = 'AccountVerification'
    ForgottenPassword = "ForgottenPassword"


class ConfirmationCode(models.Model):
    MAX_LEN_CODE = 5
    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE
    )
    code = models.CharField(max_length=MAX_LEN_CODE)
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(
        choices=ConfirmationCodeTypeChoices.choices(),
        max_length=ConfirmationCodeTypeChoices.max_len()
    )

    def __str__(self):
        return self.code


class Username(models.Model):
    username = models.CharField(
        max_length=MAX_LEN_ACCOUNT_USERNAME,
        unique=True,
        error_messages={
            'unique': "A user with this username already exists. "
        }
    )
    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name='usernames'
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()
