from server.workouts.models import ExerciseSession, WorkoutExerciseSession, SupersetSession
from django.contrib.contenttypes.models import ContentType


def get_serialized_exercises(obj):
    from server.workouts.exercise_serializers import SupersetSessionSerializerNameOnly, \
        ExerciseSessionSerializerNameOnly

    superset_serializer = SupersetSessionSerializerNameOnly
    exercise_serializer = ExerciseSessionSerializerNameOnly
    exercises = []
    for exercise in obj.exercises.all():
        exercise_instance = exercise.content_object
        if exercise.content_type.model == "supersetsession":
            exercises.append({
                "id": exercise.id,
                'type': "superset",
                'data': superset_serializer(exercise_instance).data,
            })
        elif exercise.content_type.model == "exercisesession":
            exercises.append({
                "id": exercise.id,
                'type': "exercise",
                'data': exercise_serializer(exercise_instance).data,
            })
    return exercises


def create_exercise_sessions_for_workout(request, workout_session, exercise_sessions):
    from server.workouts.models import SupersetSession
    # TODO: Refactor this function to be more readable
    # TODO: do not allow creation of empty sets
    sessions = []
    for exercise_session in exercise_sessions:
        session_type = exercise_session['session_type']
        if session_type == 'superset':
            superset_exercise_sessions = exercise_session['exercises_data']
            superset_session = SupersetSession.objects.create(created_by=request.user.profile)
            for session in superset_exercise_sessions:
                exercise = session['exercise']
                exercise_session = ExerciseSession.create_session(request, exercise['name'], exercise['id'],
                                                                  session['session_data'])
                superset_session.exercises.add(exercise_session)

            # Create WorkoutExercise relation for superset
            superset_content_type = ContentType.objects.get_for_model(SupersetSession)
            superset_workout_session = WorkoutExerciseSession.objects.create(
                content_type=superset_content_type,
                object_id=superset_session.id,
                workout_session=workout_session
            )
            superset_workout_session.save()
            sessions.append(superset_workout_session)
        elif session_type == 'exercise':
            exercise = exercise_session['exercise']
            session_data = exercise_session['session_data']
            exercise_session = ExerciseSession.create_session(request, exercise['name'], exercise['id'],
                                                              session_data)
            # Create WorkoutExercise relation for exercise
            exercise_content_type = ContentType.objects.get_for_model(ExerciseSession)
            exercise_workout_session = WorkoutExerciseSession.objects.create(
                content_type=exercise_content_type,
                object_id=exercise_session.id,
                workout_session=workout_session
            )

            exercise_workout_session.save()
            sessions.append(exercise_workout_session)
    return sessions


def calculate_exercise_set_total_volume(set_session):
    set_type = set_session.content_type.model
    if set_type == 'rest':
        return 0  # rest set has no volume
    set_instance = set_session.item
    return set_instance.weight * set_instance.reps


def calculate_exercise_total_volume(exercise_session, is_cardio=False):
    if is_cardio:
        return 0
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


def calculate_exercise_total_sets(exercise_session):
    return exercise_session.exercisesessionitem_set.count()


def calculate_superset_total_sets(superset_session):
    total_sets = 0
    for exercise in superset_session.exercises.all():
        total_sets += calculate_exercise_total_sets(exercise)
    return total_sets


def update_workout_session_exercises(request, workout_session, exercises):
    session_instance_exercises = workout_session.exercises.all()
    final_exercises = remove_exercises_not_in_list(session_instance_exercises, exercises)
    add_new_exercise_sessions_to_workout_session(request, workout_session, exercises)
    # TODO: Implement edit exercise session
    for exercise_session in final_exercises:
        exercise_data = next((exercise for exercise in exercises if exercise['id'] == exercise_session.object_id), None)
        if exercise_session.content_type.model == 'supersetsession':
            superset_session = exercise_session.content_object
            SupersetSession.edit_session(request, superset_session, exercise_data)
            continue

        ExerciseSession.edit_session(request, exercise_session, exercise_data)

    return final_exercises


def add_new_exercise_sessions_to_workout_session(request, workout_session, exercises):
    for session in exercises:
        session_type = session.get('session_type')
        # TODO: Handle the superset logic
        if session_type == 'superset':
            continue
        try:
            ExerciseSession.objects.get(pk=session['id'])
        except ExerciseSession.DoesNotExist:
            exercise = session['exercise']
            session = ExerciseSession.create_session(request, exercise['name'], exercise['id'],
                                                     exercise['session_data'])
            workout_session.add_exercise([session])



def remove_exercises_not_in_list(session_exercises: object, list_exercises: object) -> object:
    """
        Removes exercises from the workout or superset session that are not in the provided list of exercises.

        Parameters:
        session_exercises (QuerySet): The current exercises in the session.
        list_exercises (list): The new list of exercises to retain in the workout session.

        Returns:
        QuerySet: Updated QuerySet of workout session exercises.
        """
    # Extract exercise IDs from the list_exercises
    list_exercise_ids = {exercise_session.get('id') for exercise_session in list_exercises}

    # Identify exercises to be removed
    exercises_to_remove = [
        exercise for exercise in session_exercises
        if (hasattr(exercise, 'content_object') and exercise.content_object.pk not in list_exercise_ids) or
           (not hasattr(exercise, 'content_object') and exercise.pk not in list_exercise_ids)
    ]
    # exercises_to_remove = [
    #     exercise for exercise in session_exercises
    #     if exercise.content_object.pk not in list_exercise_ids
    # ]

    # Bulk delete exercises that are not in the new list
    if exercises_to_remove:
        ids_to_remove = [exercise.id for exercise in exercises_to_remove]
        session_exercises.filter(id__in=ids_to_remove).delete()

    return session_exercises
