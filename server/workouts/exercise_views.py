import time

from django.core.exceptions import ValidationError
from rest_framework import generics as rest_generic_views, status, serializers, views
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from server.utils import transform_timestamp
from server.workouts.exercise_serializers import ExerciseDetailsSerializer, BaseExerciseSerializer, \
    CreateExerciseSerializer, ExerciseSessionEditSerializer
from server.workouts.models import Exercise, ExerciseSession, Set, MuscleGroup
from .tasks import upload_exercise_video_to_cloudinary
import base64


class ExerciseDetailsView(rest_generic_views.RetrieveAPIView):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseDetailsSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


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
            video = request.data.get('video_tutorial')
            serializer = self.serializer_class(data=exercise_data)
            serializer.is_valid(raise_exception=True)
            exercise = self.perform_create(serializer)
            if to_publish:
                exercise.is_published = True
                exercise.save()

            if video:
                # Save video to a temporary location
                encoded_video = base64.b64encode(video.read()).decode('utf-8')

                # Trigger Celery task to upload video to Cloudinary
                upload_exercise_video_to_cloudinary.delay(encoded_video, exercise.id)

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



# TODO: Fix this view
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
                Set.edit_data(request,set_instance=set_instance, set_data=set)
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


        return Response("Exercise session updated successfully!", status=status.HTTP_200_OK)


class EditExerciseSessionNotesView(rest_generic_views.UpdateAPIView):
    def put(self, request, *args, **kwargs):
        session_id = kwargs.get('session_id')
        notes = request.data.get('notes')
        try:
            session = ExerciseSession.objects.get(id=session_id)
            if session.profile != request.user.profile:
                return Response(status=status.HTTP_403_FORBIDDEN)
            session.notes = notes
            session.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ExerciseSession.DoesNotExist:
            return Response("Exercise session does not exist!", status=status.HTTP_400_BAD_REQUEST)

class ExercisesByMuscleGroup(views.APIView):
    serializer_class = ExerciseDetailsSerializer
    def get(self, request):
        muscle_groups = MuscleGroup.objects.all()
        final_list = []
        for muscle_group in muscle_groups:
            muscle_group_obj = {
                "name": muscle_group.name,
                "exercises": []
            }
            for exercise in muscle_group.exercise_set.all():
                if exercise.created_by:
                    continue
                muscle_group_obj['exercises'].append(
                    self.serializer_class(exercise).data
                )
            final_list.append(muscle_group_obj)
        cardio_exercise_obj = {
            'name': "Cardio",
            "exercises": []
        }
        for exercise in Exercise.objects.filter(is_cardio=True, created_by=None or request.user.profile):
            cardio_exercise_obj['exercises'].append(self.serializer_class(exercise).data)
        final_list.append(cardio_exercise_obj)

        return Response(final_list, status=status.HTTP_200_OK)
