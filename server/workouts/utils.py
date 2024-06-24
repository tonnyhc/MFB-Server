from server.workouts.exercise_serializers import SupersetSessionSerializerNameOnly, ExerciseSessionSerializerNameOnly
from server.workouts.models import SupersetSession, ExerciseSession, WorkoutExerciseSession
from django.contrib.contenttypes.models import ContentType


def get_serialized_exercises(obj):
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
