from django.core.exceptions import ValidationError
from rest_framework import generics as rest_generic_views, status, views
from rest_framework.decorators import api_view
from rest_framework.response import Response

from server.workouts.models import WorkoutPlan, Exercise, WorkoutSession, MuscleGroup
from server.workouts.serializers import BaseWorkoutPlanSerializer, \
    WorkoutPlanDetailsSerializer, \
    WorkoutPlanCreationSerializer, WorkoutSessionDetailsSerializer, \
    BaseMuscleGroupSerializer, BaseWorkoutSerializer, WorkoutSessionEditSerializer


# Workouts
class WorkoutsByUserListView(rest_generic_views.ListAPIView):
    queryset = WorkoutPlan.objects.all()
    serializer_class = BaseWorkoutPlanSerializer

    def get(self, request, *args, **kwargs):
        query = self.queryset.filter(created_by_id=request.user.profile.id)
        serialized_query = self.serializer_class(query, many=True)
        return Response(serialized_query.data, status=status.HTTP_200_OK)


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


class WorkoutSessionEditView(rest_generic_views.UpdateAPIView):
    queryset = WorkoutSession.objects.all()
    serializer_class = WorkoutSessionEditSerializer

    def put(self, request, *args, **kwargs):
        workout_id = kwargs.get('pk')
        try:
            workout = WorkoutSession.objects.get(pk=workout_id)
        except WorkoutSession.DoesNotExist:
            return Response("Workout session does not exist.",status=status.HTTP_400_BAD_REQUEST)

        edited_session = WorkoutSession.edit_session(request, workout, request.data)
        print(self.serializer_class(edited_session).data)
        return Response(self.serializer_class(edited_session).data, status=status.HTTP_200_OK)

class WorkoutSearchView(rest_generic_views.ListAPIView):
    queryset = WorkoutSession.objects.all()
    serializer_class = WorkoutSessionDetailsSerializer

    def get(self, request, *args, **kwargs):
        profile = request.user.profile
        searched_name = request.query_params.get('name')
        all_workouts_by_name = self.queryset.filter(name__icontains=searched_name).all()
        exercises_created_by_user = all_workouts_by_name.filter(created_by=profile).all()
        exercises = all_workouts_by_name.filter(is_published=True)

        return Response({
            'workouts_by_user': self.serializer_class(exercises_created_by_user, many=True).data,
            'workouts': self.serializer_class(exercises, many=True).data
        }, status=status.HTTP_200_OK)

# Workout plans

class WorkoutPlanDetailsView(rest_generic_views.RetrieveAPIView):
    queryset = WorkoutPlan.objects.all()
    serializer_class = WorkoutPlanDetailsSerializer

    def get(self, request, *args, **kwargs):
        params_id = kwargs['id']
        query = self.queryset.get(id=params_id)
        serialized_query = self.serializer_class(query)
        return Response(serialized_query.data, status=status.HTTP_200_OK)


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
