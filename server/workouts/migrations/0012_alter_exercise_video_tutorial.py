# Generated by Django 4.2.6 on 2024-03-27 19:20

import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0011_alter_exercise_cover_photo_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exercise',
            name='video_tutorial',
            field=cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True),
        ),
    ]
