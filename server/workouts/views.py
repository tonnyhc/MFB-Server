from django.core.exceptions import ValidationError
from rest_framework import generics as rest_generic_views, status, serializers
from rest_framework.response import Response

from server.profiles.models import Profile
from server.workouts.models import WorkoutPlan, Exercise
from server.workouts.serializers import BaseWorkoutPlanSerializer, ExerciseSerializer, WorkoutPlanDetailsSerializer


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
    serializer_class = ExerciseSerializer

    def get(self, request, *args, **kwargs):
        profile = request.user.profile
        searched_name = request.query_params.get('exercise_name')
        all_exercises_by_name = self.queryset.filter(name__icontains=searched_name).all()
        exercises_created_by_user = all_exercises_by_name.filter(created_by=profile).all()
        exercises = all_exercises_by_name.filter(created_by=None)

        return Response({
            'exercises_by_user': self.serializer_class(exercises_created_by_user, many=True).data,
            'exercises': self.serializer_class(exercises, many=True).data
        }, status=status.HTTP_200_OK)


class CreateWorkoutPlanView(rest_generic_views.CreateAPIView):
    queryset = WorkoutPlan
    serializer_class = BaseWorkoutPlanSerializer

    def post(self, request, *args, **kwargs):

        try:
            WorkoutPlan.create_workout_plan(request=request, workout_plan_data=request.data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as error:
            return Response(error.message,
                            status=status.HTTP_400_BAD_REQUEST)


class CreateExerciseView(rest_generic_views.CreateAPIView):
    queryset = Exercise
    serializer_class = ExerciseSerializer

    def perform_create(self, serializer):
        user_profile = self.request.user.profile
        if not user_profile:
            return Response({'There was a problem creating the exercise, are you sure you have set up your profile?'},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer.save(created_by=user_profile)

    def post(self, request, *args, **kwargs):
        try:
            exercise_data = request.data
            serializer = self.serializer_class(data=exercise_data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
