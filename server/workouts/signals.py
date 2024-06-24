from django.db.models.signals import post_save
from django.dispatch import receiver, Signal

from server.utils import disable_signals
from server.workouts.models import WorkoutPlan, WorkoutSession


@receiver(post_save, sender=WorkoutSession)
def calculate_routine_additionals(sender, instance, created, **kwargs):
    # skipping the creation of the workout session, so the signal wont make the calculations twice
    if created:
        return

    workout_total_weight_volume = 0
    exercise_sessions = instance.exercises.all()
    for session in exercise_sessions:
        session_type = session.content_type.model
        session_instance = session.content_object

        if session_type == 'supersetsession':
            instance.total_weight_volume += calculate_superset_session_total_volume(session_instance)
            continue
        workout_total_weight_volume += calculate_exercise_total_volume(session_instance)
    instance.total_weight_volume = workout_total_weight_volume
    # disconnecting the signal, so i can save the instance without triggering the signal again and entering a recursion
    Signal.disconnect(post_save, receiver=calculate_routine_additionals, sender=WorkoutSession)

    instance.save()
    # reconnecting the signal
    Signal.connect(post_save, receiver=calculate_routine_additionals, sender=WorkoutSession)



def calculate_exercise_set_total_volume(set_session):
    set_type = set_session.content_type.model
    if set_type == 'rest':
        return 0  # rest set has no volume
    set_instance = set_session.item
    return set_instance.weight * set_instance.reps


def calculate_exercise_total_volume(exercise_session):
    total_volume = 0
    session_set_items = exercise_session.exercisesessionitem_set.all()
    for set_session in session_set_items:
        total_volume += calculate_exercise_set_total_volume(set_session)
    return total_volume


def calculate_superset_session_total_volume(superset_session):
    total_volume = 0
    superset_exercises = superset_session.exercises.all()
    for exercise in superset_exercises:
        total_volume += calculate_exercise_total_volume(exercise)
    return total_volume
