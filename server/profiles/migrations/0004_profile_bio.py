# Generated by Django 4.2.6 on 2024-04-20 13:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0003_alter_profile_birthday'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='bio',
            field=models.TextField(blank=True, max_length=150, null=True),
        ),
    ]
