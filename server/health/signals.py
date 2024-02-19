from django.db.models.signals import post_save
from django.dispatch import receiver

from server.health.models import Measures, Fitness
from server.profiles.models import Profile


@receiver(post_save, sender=Profile)
def create_measure_and_fitness(sender, instance, created, **kwargs):
    if created:
        print('entered signal')

        Measures.objects.create(profile=instance)
        Fitness.objects.create(profile=instance)
