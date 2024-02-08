from django.core.exceptions import ValidationError
from rest_framework import generics as rest_generic_views, status, serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from server.map_data import empty_set
from server.profiles.models import Profile
from server.workouts.models import WorkoutPlan, Exercise, WorkoutSession, ExerciseSession, Set
from server.workouts.serializers import BaseWorkoutPlanSerializer, CreateExerciseSerializer, \
    WorkoutPlanDetailsSerializer, \
    WorkoutPlanCreationSerializer, BaseExerciseSerializer, BaseWorkoutSessionSerializer, WorkoutSessionDetailsSerializer


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
            print(exercise)
            if to_publish:
                exercise.is_published = True
                exercise.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class WorkoutSessionDetailsView(rest_generic_views.RetrieveAPIView):
    queryset = WorkoutSession.objects.all()
    serializer_class = WorkoutSessionDetailsSerializer

    def get(self, request, *args, **kwargs):
        params_id = kwargs['id']
        filtered_query = self.queryset.filter(id=params_id).get()
        serialized_query = self.serializer_class(filtered_query)

        return Response(serialized_query.data, status=status.HTTP_200_OK)


class AddSetToExerciseSession(rest_generic_views.CreateAPIView):
    def post(self, request, *args, **kwargs):
        session_id = kwargs.get('session_id')
        try:
            exercise_session = ExerciseSession.objects.get(id=session_id)
            ExerciseSession.add_single_set_instance(request, exercise_session, empty_set)
            return Response(status=status.HTTP_204_NO_CONTENT)
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
