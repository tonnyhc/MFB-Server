# Generated by Django 4.2.6 on 2024-06-22 19:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('workouts', '0024_activeroutine'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workoutsession',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='workoutsession',
            name='object_id',
        ),
        migrations.CreateModel(
            name='WorkoutExerciseSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('workout_session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workout_exercises', to='workouts.workoutsession')),
            ],
        ),
        migrations.AddField(
            model_name='workoutsession',
            name='exercises',
            field=models.ManyToManyField(related_name='workout_sessions', to='workouts.workoutexercisesession'),
        ),
    ]
