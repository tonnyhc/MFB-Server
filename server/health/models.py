from django.db import models

from server.profiles.models import Profile

from enum import Enum

from server.mixins import ChoicesEnumMixin


class ActivityChoicesMixin(ChoicesEnumMixin, Enum):
    Sedentary = "Sedentary"
    Light = "Light"
    Moderate = "Moderate"
    Very = "Very"
    Extreme = "Extreme"


class FitnessGoalChoices(ChoicesEnumMixin, Enum):
    Bulk = "Bulk"
    Cut = "Cut"
    Maintain = "Maintain"


class Measures(models.Model):
    height = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    weight = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    activity = models.CharField(
        choices=ActivityChoicesMixin.choices(),
        max_length=ActivityChoicesMixin.max_len(),
        blank=True,
        null=True
    )
    goal = models.CharField(
        choices=FitnessGoalChoices.choices(),
        max_length=FitnessGoalChoices.max_len(),
        blank=True,
        null=True
    )
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE
    )
