from enum import Enum

from cloudinary.models import CloudinaryField
from django.contrib.auth import get_user_model
from django.db import models

from server.mixins import ChoicesEnumMixin
from server.models_utils import MAX_LEN_PROFILE_FULL_NAME, MAX_LEN_PROFILE_BIO

UserModel = get_user_model()


class GenderChoices(ChoicesEnumMixin, Enum):
    Man = "Man"
    Woman = "Woman"


class ProfileManager(models.Manager):
    def create_profile(self, user):
        profile = self.model(
            user=user
        )
        profile.save()
        return profile


class Profile(models.Model):
    full_name = models.CharField(
        max_length=MAX_LEN_PROFILE_FULL_NAME,
        blank=True
    )
    gender = models.CharField(
        choices=GenderChoices.choices(),
        max_length=GenderChoices.max_len(),
    blank = True
    )
    user = models.OneToOneField(
        UserModel,
        on_delete=models.CASCADE
    )
    birthday = models.DateField(
        blank=True,
        null=True
    )
    bio = models.TextField(
        max_length=MAX_LEN_PROFILE_BIO,
        blank=True,
        null=True
    )
    picture = CloudinaryField("image", blank=True, null=True)

    objects = ProfileManager()
