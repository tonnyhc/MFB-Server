# Generated by Django 4.2.6 on 2024-02-10 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0005_workoutsession_is_published'),
    ]

    operations = [
        migrations.AddField(
            model_name='set',
            name='set_index',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
