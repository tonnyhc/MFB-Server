# Generated by Django 4.2.6 on 2024-01-03 16:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0003_set_created_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercise',
            name='is_published',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='set',
            name='bodyweight',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='set',
            name='to_failure',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='set',
            name='reps',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='set',
            name='weight',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
