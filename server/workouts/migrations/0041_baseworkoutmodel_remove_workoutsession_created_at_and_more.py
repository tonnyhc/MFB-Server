# Generated by Django 4.2.6 on 2024-12-22 14:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0006_alter_profile_full_name_alter_profile_gender'),
        ('workouts', '0040_remove_exerciseinstruction_exercise_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseWorkoutModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('total_exercises', models.IntegerField()),
                ('total_sets', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='profiles.profile')),
            ],
        ),
        migrations.RemoveField(
            model_name='workoutsession',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='workoutsession',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='workoutsession',
            name='id',
        ),
        migrations.RemoveField(
            model_name='workoutsession',
            name='is_published',
        ),
        migrations.RemoveField(
            model_name='workoutsession',
            name='name',
        ),
        migrations.RemoveField(
            model_name='workoutsession',
            name='total_exercises',
        ),
        migrations.RemoveField(
            model_name='workoutsession',
            name='total_sets',
        ),
        migrations.AddField(
            model_name='workoutsession',
            name='baseworkoutmodel_ptr',
            field=models.OneToOneField(auto_created=True, default=1, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='workouts.baseworkoutmodel'),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='WorkoutTemplate',
            fields=[
                ('baseworkoutmodel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='workouts.baseworkoutmodel')),
                ('is_published', models.BooleanField(default=True)),
                ('exercises', models.ManyToManyField(related_name='template_exercises', to='workouts.workoutexercisesession')),
            ],
            bases=('workouts.baseworkoutmodel',),
        ),
    ]
