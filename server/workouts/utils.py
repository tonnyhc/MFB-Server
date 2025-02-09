from server.workouts.models import WorkoutTemplate, WorkoutTemplateExerciseItem, WorkoutSession


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
    # TODO: do not allow creation of empty sets
    sessions = []

    for exercise_session in exercise_sessions:
        session_type = exercise_session.get('session_type')

        if session_type == 'superset':
            superset_workout_session = create_superset_workout_session(request, workout_session, exercise_session)
            sessions.append(superset_workout_session)
        elif session_type == 'exercise':
            exercise_workout_session = create_exercise_workout_session(request, workout_session, exercise_session)
            sessions.append(exercise_workout_session)

    return sessions


def create_exercise_workout_session(request, workout_session, exercise_session):
    from server.workouts.models import ExerciseSession, WorkoutExerciseSession
    from django.contrib.contenttypes.models import ContentType
    session_order = exercise_session.get('order', 0)
    exercise = exercise_session['exercise']
    session_data = exercise_session['session_data']
    exercise_session = ExerciseSession.create_session(
        request, exercise['name'], exercise['id'], session_data
    )

    exercise_content_type = ContentType.objects.get_for_model(ExerciseSession)
    if isinstance(workout_session, WorkoutTemplate):
        exercise_workout_session = WorkoutTemplateExerciseItem.objects.create(
            content_type=exercise_content_type,
            object_id=exercise_session.id,
            workout_template=workout_session,
            order=session_order or 0
        )
    elif isinstance(workout_session, WorkoutSession):
        exercise_workout_session = WorkoutExerciseSession.objects.create(
            content_type=exercise_content_type,
            object_id=exercise_session.id,
            workout_session=workout_session,
            order=session_order or 0
        )

    exercise_workout_session.save()
    return exercise_workout_session


def create_superset_workout_session(request, workout_session, exercise_session):
    from server.workouts.models import SupersetSession, ExerciseSession, WorkoutExerciseSession
    from django.contrib.contenttypes.models import ContentType

    superset_exercise_sessions = exercise_session['exercises']
    superset_session = SupersetSession.objects.create(created_by=request.user.profile)
    superset_order_index = exercise_session.get('order')
    for session in superset_exercise_sessions:
        exercise = session['exercise']
        exercise_session = ExerciseSession.create_session(
            request, exercise['name'], exercise['id'], session['session_data']
        )
        superset_session.exercises.add(exercise_session)
    superset_content_type = ContentType.objects.get_for_model(SupersetSession)
    superset_workout_session = WorkoutExerciseSession.objects.create(
        content_type=superset_content_type,
        object_id=superset_session.id,
        workout_session=workout_session,
        order=superset_order_index
    )

    superset_workout_session.save()
    return superset_workout_session


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
    from server.workouts.models import ExerciseSession, SupersetSession
    session_instance_exercises = workout_session.exercises.all()
    # final_exercises_test = remove_exercises_not_in_list_test(session_instance_exercises, exercises)
    final_exercises = remove_exercises_not_in_list(session_instance_exercises, exercises)

    exercises_to_add = add_new_exercise_sessions_to_workout_session(request, workout_session, exercises)
    # # TODO: Implement edit exercise session
    for exercise_session in final_exercises:
        exercise_data = next((exercise for exercise in exercises if exercise['id'] == exercise_session.object_id), None)
        if exercise_session.content_type.model == 'supersetsession':
            superset_session = exercise_session.content_object
            SupersetSession.edit_session(request, superset_session, exercise_data)
            continue

        ExerciseSession.edit_session(request, exercise_session, exercise_data)
    # workout_session.add_exercise_sessions(exercises_to_add)
    workout_session.exercises.add(*exercises_to_add)
    workout_session.save()

    return final_exercises


def add_new_exercise_sessions_to_workout_session(request, workout_session, exercises):
    from server.workouts.models import ExerciseSession
    new_exercises = []
    for session in exercises:
        session_type = session.get('session_type')
        session_id = session.get('id')
        exercise = session.get('exercise')
        # TODO: Handle the superset logic
        if session_type == 'superset':
            continue
        try:
            if isinstance(session_id, int):
                ExerciseSession.objects.get(pk=session_id)
            else:
                raise ExerciseSession.DoesNotExist
        except ExerciseSession.DoesNotExist:
            new_session = create_exercise_workout_session(request, workout_session, session)
            new_exercises.append(new_session)
    return new_exercises


def remove_exercises_not_in_list_old(session_exercises: object, list_exercises: object) -> object:
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

    exercises_to_remove = [
        exercise for exercise in session_exercises
        if (getattr(exercise.content_object, 'pk', exercise.pk) not in list_exercise_ids)
    ]

    # Identify exercises to be removed
    # exercises_to_remove = [
    #     exercise for exercise in session_exercises
    #     if (hasattr(exercise, 'content_object') and exercise.content_object.pk not in list_exercise_ids) or
    #        (not hasattr(exercise, 'content_object') and exercise.pk not in list_exercise_ids)
    # ]

    # Bulk delete exercises that are not in the new list
    if exercises_to_remove:
        ids_to_remove = [exercise.id for exercise in exercises_to_remove]
        session_exercises.filter(id__in=ids_to_remove).delete()

    return session_exercises


def remove_exercises_not_in_list(session_exercises: object, list_exercises: object) -> object:
    list_exercise_ids = {exercise_session.get('id') for exercise_session in list_exercises}
    session_exercise_ids = {exercise_session.content_object.pk for exercise_session in session_exercises}
    for session_exercise_id in session_exercise_ids:
        if session_exercise_id not in list_exercise_ids:
            session_exercises.filter(id=session_exercise_id).delete()
    return session_exercises



def convert_str_to_float(value):
    if ',' in str(value):
        value = value.replace(",", ".")
    return float(value)


def convert_str_time_to_interval_time(time: str) -> dict:
    try:
        # Split the time string into components
        time_parts = time.split(':')
        hours, minutes, seconds = (time_parts + ['0', '0', '0'])[:3]

        # Convert each component to an integer, defaulting to 0 if empty or null
        hours = int(hours) if hours else 0
        minutes = int(minutes) if minutes else 0
        seconds = int(seconds) if seconds else 0

        # Return the components in a dictionary
        return {'hours': hours, 'minutes': minutes, 'seconds': seconds}
    except Exception as e:
        print(f"Error in converting time: {e}")
        return {'hours': 0, 'minutes': 0, 'seconds': 0}


def get_value_or_default(data: dict, key: str, default=0):
    value = data.get(key, default)
    return value if value != '' else default


def serializer_exericses_for_session_or_template(exercises, exercise_serializer, superset_serializer):
    """
       Serialize a list of exercises based on their type (ExerciseSession or SupersetSession).
       """
    serialized_exercises = []
    for exercise in exercises:
        exercise_type = exercise.content_type.model
        exercise_instance = exercise.content_object
        if exercise_type == 'exercisesession':
            serialized_exercises.append(exercise_serializer(exercise_instance).data)
        elif exercise_type == 'supersetsession':
            serialized_exercises.append(superset_serializer(exercise_instance).data)
    return serialized_exercises
