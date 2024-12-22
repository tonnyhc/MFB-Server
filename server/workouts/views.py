import time

from django.core.exceptions import ValidationError
from rest_framework import generics as rest_generic_views, status, views
from rest_framework.decorators import api_view
from rest_framework.response import Response

from server.workouts.models import WorkoutPlan, Exercise, WorkoutSession, MuscleGroup
from server.workouts.serializers import \
    WorkoutPlanCreationSerializer, WorkoutSessionDetailsSerializer, \
    BaseMuscleGroupSerializer, RoutinesListSerializer, \
    RoutineDetailsSerializer, BaseWorkoutSessionSerializer, WorkoutListSerializer


# Workouts
class RoutinesListView(rest_generic_views.ListAPIView):
    queryset = WorkoutPlan.objects.all()
    serializer_class = RoutinesListSerializer

    def get(self, request, *args, **kwargs):
        query = self.queryset.filter(created_by_id=request.user.profile.id).order_by('-created_at')
        serialized_query = self.serializer_class(query, many=True, context={'request': request})
        return Response(serialized_query.data, status=status.HTTP_200_OK)


class WorkoutsListView(rest_generic_views.ListAPIView):
    queryset = WorkoutSession.objects.all()
    serializer_class = WorkoutListSerializer
    def get(self, request, *args, **kwargs):
        query = self.queryset.filter(created_by_id=request.user.profile.id).order_by('-created_at')
        serialized_query = self.serializer_class(query, many=True, context={'request': request})
        return Response(serialized_query.data, status=status.HTTP_200_OK)


class CreateWorkoutView(rest_generic_views.CreateAPIView):
    serializer_class = BaseWorkoutSessionSerializer
    details_serializer = WorkoutSessionDetailsSerializer

    def post(self, request, *args, **kwargs):
        print(request.data)
        workout_name = request.data.get('name')
        exercises = request.data.get('exercises')
        if not workout_name:
            return Response({'name': "Please provide a name for your workout!"}, status=status.HTTP_400_BAD_REQUEST)
        if not exercises:
            return Response({"exercises": "The workout must contain exercises!"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            workout = WorkoutSession.create_session(request, workout_name, exercises)
            return Response(self.details_serializer(workout).data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({"generic": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"generic": 'There was a problem creating the workout: ' + str(e)},
                            status=status.HTTP_400_BAD_REQUEST)


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
    serializer_class = WorkoutSessionDetailsSerializer

    def put(self, request, *args, **kwargs):
        workout_id = kwargs.get('pk')
        try:
            workout = WorkoutSession.objects.get(pk=workout_id)
        except WorkoutSession.DoesNotExist:

            return Response("Workout session does not exist.", status=status.HTTP_400_BAD_REQUEST)
        edited_session = WorkoutSession.edit_session(request, workout, request.data)

        return Response(self.serializer_class(edited_session).data, status=status.HTTP_200_OK)


class WorkoutSessionDeleteView(rest_generic_views.DestroyAPIView):
    def delete(self, request, *args, **kwargs):
        workout_id = kwargs.get('pk')
        try:
            workout = WorkoutSession.objects.get(pk=workout_id)
        except WorkoutSession.DoesNotExist:
            return Response("Workout session does not exist.", status=status.HTTP_400_BAD_REQUEST)
        if request.user.profile != workout.created_by:
            return Response("You can only delete your own workouts!", status=status.HTTP_401_UNAUTHORIZED)
        workout.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
    serializer_class = RoutineDetailsSerializer

    def get(self, request, *args, **kwargs):
        params_id = kwargs['id']
        query = self.queryset.get(id=params_id)
        serialized_query = self.serializer_class(query)
        return Response(serialized_query.data, status=status.HTTP_200_OK)


class CreateRoutineView(rest_generic_views.CreateAPIView):
    queryset = WorkoutPlan
    serializer_class = WorkoutPlanCreationSerializer

    @staticmethod
    def validate_workout_plan_data(data):
        if "workouts" not in data or len(data['workouts']) <= 0:
            return Response("Workout plan must have workouts", status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        print(request.data)
        validation_response = self.validate_workout_plan_data(request.data)

        if validation_response:
            return validation_response
        try:
            WorkoutPlan.create_routine(request=request, routine_data=request.data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as error:
            return Response(error.message,
                            status=status.HTTP_400_BAD_REQUEST)


class AddWorkoutToRoutineView(rest_generic_views.UpdateAPIView):
    def put(self, request, *args, **kwargs):
        workout_plan_id = kwargs.get('id')
        workout_id = request.data.get('workout_id')
        try:
            workout_plan = WorkoutPlan.objects.get(pk=workout_plan_id)
            workout = WorkoutSession.objects.get(pk=workout_id)
        except WorkoutPlan.DoesNotExist:
            return Response("Workout plan does not exist.", status=status.HTTP_400_BAD_REQUEST)
        except WorkoutSession.DoesNotExist:
            return Response("Workout does not exist.", status=status.HTTP_400_BAD_REQUEST)
        if workout_plan.created_by != request.user.profile:
            return Response("You can only add workouts to your own workout plans!", status=status.HTTP_401_UNAUTHORIZED)
        workout_plan.workouts.add(workout)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DeleteWorkoutPlanView(rest_generic_views.DestroyAPIView):
    queryset = WorkoutPlan

    def delete(self, request, *args, **kwargs):
        workout_plan = WorkoutPlan.objects.get(pk=kwargs['id'])
        request_user_profile = request.user.profile
        if request_user_profile == workout_plan.created_by:
            workout_plan.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response("You can only delete your own workouts!", status=status.HTTP_401_UNAUTHORIZED)


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

    def get(self, request, *args, **kwargs):
        ordered_muscle_groups = self.queryset.order_by('name')
        return Response({
            'muscle_groups': self.serializer_class(ordered_muscle_groups, many=True).data
        })


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
