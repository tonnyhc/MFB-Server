# Generated by Django 4.2.6 on 2024-06-05 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0017_alter_exercise_is_cardio'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercise',
            name='bodyweight',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
