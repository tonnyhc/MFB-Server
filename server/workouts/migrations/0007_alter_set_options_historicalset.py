# Generated by Django 4.2.6 on 2024-02-10 11:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('profiles', '0001_initial'),
        ('workouts', '0006_set_set_index'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='set',
            options={'ordering': ['set_index']},
        ),
        migrations.CreateModel(
            name='HistoricalSet',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('weight', models.FloatField(blank=True, null=True)),
                ('reps', models.IntegerField(blank=True, null=True)),
                ('min_reps', models.IntegerField(blank=True, null=True)),
                ('max_reps', models.IntegerField(blank=True, null=True)),
                ('to_failure', models.BooleanField(default=False)),
                ('bodyweight', models.BooleanField(default=False)),
                ('set_index', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('created_by', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='profiles.profile')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical set',
                'verbose_name_plural': 'historical sets',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
