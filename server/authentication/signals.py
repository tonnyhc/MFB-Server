from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from server.authentication.models import Username

UserModel = get_user_model()


@receiver(post_save, sender=UserModel)
def create_username_instance(sender, instance, created, **kwargs):
    if created:
        Username.objects.create(username=instance.username, user=instance)

@receiver(pre_save, sender=UserModel)
def update_username_instance(sender, instance, **kwargs):
    if instance.pk:  # Check if the instance is already saved in the database
        try:
            old_instance = UserModel.objects.get(pk=instance.pk)
            if old_instance.username != instance.username:
                # If the username has changed, update the existing Username instance
                username_record = Username.objects.get(user=instance)
                username_record.username = instance.username
                username_record.save()
        except UserModel.DoesNotExist:
            pass  # Handle the case where the user doesn't exist (unlikely)
        except Username.DoesNotExist:
            # Handle the case where the Username record doesn't exist
            Username.objects.create(username=instance.username, user=instance)