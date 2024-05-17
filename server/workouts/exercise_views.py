from django.core.exceptions import ValidationError
from rest_framework import generics as rest_generic_views, status, serializers, views
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from server.utils import transform_timestamp
from server.workouts.exercise_serializers import ExerciseDetailsSerializer, BaseExerciseSerializer, \
    CreateExerciseSerializer, ExerciseSessionEditSerializer
from server.workouts.models import Exercise, ExerciseSession, Set


class ExerciseDetailsView(rest_generic_views.RetrieveAPIView):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseDetailsSerializer


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


class EditExerciseSessionView(rest_generic_views.UpdateAPIView):
    serializer_class = ExerciseSessionEditSerializer

    def put(self, request, *args, **kwargs):
        session_id = kwargs.get('session_id')
        sets = request.data.get('sets')
        try:
            session = ExerciseSession.objects.get(id=session_id)
        except ExerciseSession.DoesNotExist:
            return Response("Exercise session does not exist!", status=status.HTTP_400_BAD_REQUEST)
        if session.profile != request.user.profile:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        session.sets.all().delete()
        for set in sets:
            try:
                set_instance = Set.objects.get(id=set.get('id'))
                Set.edit_data(set_instance=set_instance, set_data=set)
                set_instance.save()
            except Set.DoesNotExist:
                try:
                    set_instance = ExerciseSession.add_single_set_instance(request=self.request,
                                                                           exercise_session=session, set_data=set)

                except ValidationError as e:
                    return Response(e.message, status=status.HTTP_400_BAD_REQUEST)
                set_instance.save()
                session.save()
        session.save()

        print(session.sets.all())

        return Response("Exercise session updated successfully!", status=status.HTTP_200_OK)
