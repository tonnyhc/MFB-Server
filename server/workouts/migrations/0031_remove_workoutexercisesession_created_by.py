# Generated by Django 4.2.6 on 2024-06-28 18:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0030_alter_workoutexercisesession_options_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workoutexercisesession',
            name='created_by',
        ),
    ]
