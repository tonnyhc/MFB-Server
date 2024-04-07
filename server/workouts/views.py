from django.core.exceptions import ValidationError
from rest_framework import generics as rest_generic_views, status, serializers, views
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from server.map_data import empty_set
from server.utils import transform_timestamp
from server.workouts.models import WorkoutPlan, Exercise, WorkoutSession, ExerciseSession, Set, MuscleGroup
from server.workouts.serializers import BaseWorkoutPlanSerializer, CreateExerciseSerializer, \
    WorkoutPlanDetailsSerializer, \
    WorkoutPlanCreationSerializer, BaseExerciseSerializer, BaseWorkoutSessionSerializer, \
    WorkoutSessionDetailsSerializer, BaseSetSerializer, SetDetailsSerializer, EditSetSerializer, \
    BaseMuscleGroupSerializer, BaseWorkoutSerializer


class WorkoutsByUserListView(rest_generic_views.ListAPIView):
    queryset = WorkoutPlan.objects.all()
    serializer_class = BaseWorkoutPlanSerializer

    def get(self, request, *args, **kwargs):
        query = self.queryset.filter(created_by_id=request.user.profile.id)
        serialized_query = self.serializer_class(query, many=True)
        return Response(serialized_query.data, status=status.HTTP_200_OK)


class WorkoutPlanDetailsView(rest_generic_views.RetrieveAPIView):
    queryset = WorkoutPlan.objects.all()
    serializer_class = WorkoutPlanDetailsSerializer

    def get(self, request, *args, **kwargs):
        params_id = kwargs['id']
        query = self.queryset.get(id=params_id)
        serialized_query = self.serializer_class(query)
        return Response(serialized_query.data, status=status.HTTP_200_OK)


class SearchExerciseView(rest_generic_views.ListAPIView):
    queryset = Exercise.objects.all()
    serializer_class = BaseExerciseSerializer

    def get(self, request, *args, **kwargs):
        profile = request.user.profile
        searched_name = request.query_params.get('name')
        all_exercises_by_name = self.queryset.filter(name__icontains=searched_name).all()
        exercises_created_by_user = all_exercises_by_name.filter(created_by=profile).all()
        exercises = all_exercises_by_name.filter(is_published=True)

        return Response({
            'exercises_by_user': self.serializer_class(exercises_created_by_user, many=True).data,
            'exercises': self.serializer_class(exercises, many=True).data
        }, status=status.HTTP_200_OK)


class CreateWorkoutPlanView(rest_generic_views.CreateAPIView):
    queryset = WorkoutPlan
    serializer_class = WorkoutPlanCreationSerializer

    @staticmethod
    def validate_workout_plan_data(data):
        if "workouts" not in data:
            return Response("Workout plan must have workouts", status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        validation_response = self.validate_workout_plan_data(request.data)
        if validation_response:
            return validation_response
        try:
            WorkoutPlan.create_workout_plan(request=request, workout_plan_data=request.data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as error:
            return Response(error.message,
                            status=status.HTTP_400_BAD_REQUEST)


class CreateExerciseView(rest_generic_views.CreateAPIView):
    queryset = Exercise
    serializer_class = CreateExerciseSerializer
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        user_profile = self.request.user.profile
        if not user_profile:
            return Response({'There was a problem creating the exercise, are you sure you have set up your profile?'},
                            status=status.HTTP_400_BAD_REQUEST)

        return serializer.save(created_by=user_profile)

    def post(self, request, *args, **kwargs):
        try:
            exercise_data = request.data

            to_publish = request.data.get('publish')
            serializer = self.serializer_class(data=exercise_data)
            serializer.is_valid(raise_exception=True)
            exercise = self.perform_create(serializer)
            if to_publish:
                exercise.is_published = True
                exercise.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CreateWorkoutView(rest_generic_views.CreateAPIView):
    serializer_class = BaseWorkoutSerializer

    def post(self, request, *args, **kwargs):
        workout_name = request.data.get('name')
        exercises = request.data.get('exercises')
        if not workout_name:
            return Response("Please provide a name for your workout!", status=status.HTTP_400_BAD_REQUEST)
        if not exercises:
            return Response("The workout must contain exercises!", status=status.HTTP_400_BAD_REQUEST)

        try:
            workout = WorkoutSession.create_session(request, workout_name, exercises)
            return Response(self.serializer_class(workout).data, status=status.HTTP_200_OK)
        except ValidationError:
            return Response('There was a problem creating the workout', status=status.HTTP_400_BAD_REQUEST)


class WorkoutSessionDetailsView(rest_generic_views.RetrieveAPIView):
    queryset = WorkoutSession.objects.all()
    serializer_class = WorkoutSessionDetailsSerializer

    def get(self, request, *args, **kwargs):
        params_id = kwargs['id']
        filtered_query = self.queryset.filter(id=params_id).get()
        serialized_query = self.serializer_class(filtered_query)

        return Response(serialized_query.data, status=status.HTTP_200_OK)


class AddSetToExerciseSession(rest_generic_views.CreateAPIView):
    serializer_class = SetDetailsSerializer

    def post(self, request, *args, **kwargs):
        session_id = kwargs.get('session_id')
        try:
            exercise_session = ExerciseSession.objects.get(id=session_id)
            new_set_instance = ExerciseSession.add_single_set_instance(request, exercise_session, empty_set)
            serialized_set = self.serializer_class(new_set_instance)
            return Response(serialized_set.data, status=status.HTTP_200_OK)
        except ExerciseSession.DoesNotExist:
            return Response("Invalid exercise session", status=status.HTTP_400_BAD_REQUEST)


class RemoveSetFromExerciseSession(rest_generic_views.DestroyAPIView):
    def post(self, request, *args, **kwargs):
        set_id = kwargs.get('set_id')
        try:
            set_instance = Set.objects.get(id=set_id)
            set_creator = set_instance.created_by
            request_profile = request.user.profile
            if set_creator != request_profile:
                return Response('You can only delete your own sets.', status=status.HTTP_401_UNAUTHORIZED)
            set_instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Set.DoesNotExist:
            return Response('Cant delete not existing set.', status=status.HTTP_400_BAD_REQUEST)


class EditSet(views.APIView):
    queryset = Set.objects.all()
    serializer_class = EditSetSerializer

    def post(self, request, *args, **kwargs):
        set_id = kwargs.get('set_id')
        try:
            set_instance = self.queryset.get(id=set_id)
            data = request.data

            def convert_str_to_float(value):
                if ',' in value:
                    value = value.replace(",", ".")
                return float(value)

            weight = data.get('weight')
            converted_weight = convert_str_to_float(weight)
            set_obj = {
                'reps': str(data.get('reps')),
                "weight": converted_weight,
                "max_reps": str(data.get('maxReps')),
                "min_reps": str(data.get('minReps')),
                "to_failure": data.get('failure'),
                "bodyweight": data.get('bodyweight'),
                'created_by': set_instance.created_by.pk
            }
            serializer = self.serializer_class(data=set_obj)
            serializer.is_valid(raise_exception=True)

            updated_instance = Set.edit_data(request, set_instance, set_obj)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Set.DoesNotExist:
            return Response('There was an error updating the set!', status=status.HTTP_400_BAD_REQUEST)


class GetExerciseProgress(views.APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        session_id = kwargs.get('session_id')
        try:
            exercise_session = ExerciseSession.objects.get(id=session_id)
        except ExerciseSession.DoesNotExist:
            return Response("Exercise session does not exist!", status=status.HTTP_400_BAD_REQUEST)
        sets = exercise_session.sets.all()
        return_array = []
        for set in sets:
            if len(set.history.all()) > 0:
                set_history_array = []
                for set_history in set.history.all()[::-1]:
                    set_history_array.append({
                        'weight': set_history.weight,
                        'updated_at': transform_timestamp(str(set_history.updated_at))
                    })
                return_array.append(set_history_array)
            return_array.append([])
        return Response(return_array, status=status.HTTP_200_OK)


# @api_view(["GET"])
# @authentication_classes([TokenAuthentication])
# @permission_classes([IsAuthenticated])
# def get_exercise_progress(request, session_id):
#     print(request.user)
#     try:
#         exercise_session = ExerciseSession.objects.get(id=session_id)
#     except ExerciseSession.DoesNotExist:
#         return Response("Exercise session does not exist!", status=status.HTTP_400_BAD_REQUEST)
#     sets = exercise_session.sets.all()
#     return_array = []
#     for set in sets:
#         if len(set.history.all()) > 0:
#             set_history_array = []
#             for set_history in set.history.all()[::-1]:
#                 set_history_array.append({
#                     'weight': set_history.weight,
#                     'updated_at': transform_timestamp(str(set_history.updated_at))
#                 })
#             return_array.append(set_history_array)
#         return_array.append([])
#     return Response(return_array, status=status.HTTP_200_OK)


class MuscleGroupsListView(rest_generic_views.ListAPIView):
    queryset = MuscleGroup.objects.all()
    serializer_class = BaseMuscleGroupSerializer


class ExercisesByMuscleGroup(views.APIView):

    def get(self, request):
        muscle_groups = MuscleGroup.objects.all()
        final_list = []
        for muscle_group in muscle_groups:
            # TODO: Fix this so it returns only the built ins
            muscle_group_obj = {
                "name": muscle_group.name,
                "exercises": []
            }
            for exercise in muscle_group.exercise_set.all():
                muscle_group_obj['exercises'].append({
                    'name': exercise.name,
                    'id': exercise.id
                })
            final_list.append(muscle_group_obj)
        return Response(final_list, status=status.HTTP_200_OK)


@api_view(['POST'])
def publish_exercise(exercise, exercise_id):
    if exercise:
        exercise.is_published = True
        exercise.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    try:
        exercise = Exercise.objects.filter(id=exercise_id).get()
        exercise.is_published = True
        exercise.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Exercise.DoesNotExist:
        return Response('There was a problem publishing the exercise, as it seems to not exist.',
                        status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def publish_workout(request):
    workout_id = request.query_params.get('id')
    WorkoutSession.publish_workout(workout_id)
