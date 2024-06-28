from django.db.models.signals import post_save
from django.dispatch import receiver, Signal

from server.workouts.models import WorkoutPlan, WorkoutSession
from server.workouts.utils import calculate_superset_session_total_volume, calculate_exercise_total_volume, \
    calculate_superset_total_sets, calculate_exercise_total_sets


@receiver(post_save, sender=WorkoutSession)
def calculate_routine_additions(sender, instance, created, **kwargs):
    # NOTE: this is a workaround, the signal should not be triggered when the instance is created,
    # because the workout does not have a data yet
    if created:
        return

    workout_total_weight_volume = 0
    workout_total_sets = 0
    exercise_sessions = instance.exercises.all()
    for session in exercise_sessions:
        session_type = session.content_type.model
        session_instance = session.content_object

        if session_type == 'supersetsession':
            workout_total_weight_volume += calculate_superset_session_total_volume(session_instance)
            workout_total_sets += calculate_superset_total_sets(session_instance)
            continue
        is_exercise_cardio = False
        exercise_session_items = session_instance.exercisesessionitem_set.all()
        if len(exercise_session_items) > 0:
            is_exercise_cardio = exercise_session_items.first().content_type.model == 'interval'
        workout_total_weight_volume += calculate_exercise_total_volume(session_instance, is_exercise_cardio)
        workout_total_sets += calculate_exercise_total_sets(session_instance)

    instance.total_weight_volume = workout_total_weight_volume
    instance.total_sets = workout_total_sets
    # disconnecting the signal, so i can save the instance without triggering the signal again and entering a recursion
    Signal.disconnect(post_save, receiver=calculate_routine_additions, sender=WorkoutSession)

    instance.save()
    # reconnecting the signal
    Signal.connect(post_save, receiver=calculate_routine_additions, sender=WorkoutSession)
