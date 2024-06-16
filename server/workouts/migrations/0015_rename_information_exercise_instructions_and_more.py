# Generated by Django 4.2.6 on 2024-06-02 20:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0014_remove_exercise_cover_photo_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='exercise',
            old_name='information',
            new_name='instructions',
        ),
        migrations.RemoveField(
            model_name='exercise',
            name='tips',
        ),
        migrations.AddField(
            model_name='exercise',
            name='tips_and_tricks',
            field=models.TextField(blank=True, max_length=255, null=True),
        ),
    ]
