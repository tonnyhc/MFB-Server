# Generated by Django 4.2.6 on 2023-12-18 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0006_alter_confirmationcode_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='confirmationcode',
            name='type',
            field=models.CharField(choices=[('AccountVerification', 'AccountVerification'), ('ForgottenPassword', 'ForgottenPassword')], max_length=20),
        ),
    ]
