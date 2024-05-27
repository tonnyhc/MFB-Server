from django.core.validators import MinValueValidator
from django.db import models
from simple_history.models import HistoricalRecords

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
    weight = models.FloatField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(0.0)
        ]
    )

    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE
    )

    history = HistoricalRecords()

    def __str__(self):
        return self.profile.user.username


class Fitness(models.Model):
    activity = models.CharField(
        choices=ActivityChoicesMixin.choices(),
        max_length=ActivityChoicesMixin.max_len(),
        blank=True,
        null=True
    )
    # TODO: Fix the goal's max_len
    goal = models.CharField(
        choices=FitnessGoalChoices.choices(),
        # max_length=FitnessGoalChoices.max_len(),
        max_length=50,
        blank=True,
        null=True,
    )
    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.profile.user.username
