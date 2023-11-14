from enum import Enum

from django.contrib.auth import get_user_model
from django.db import models

from server.mixins import ChoicesEnumMixin

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
    MAX_LEN_FULL_NAME = 150
    full_name = models.CharField(
        max_length=MAX_LEN_FULL_NAME,
    )
    gender = models.CharField(
        choices=GenderChoices.choices(),
        max_length=GenderChoices.max_len()
    )
    user = models.OneToOneField(
        UserModel,
        on_delete=models.CASCADE
    )

    objects = ProfileManager()