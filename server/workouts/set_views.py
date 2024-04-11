from rest_framework import generics as rest_generic_views, status, views
from rest_framework.response import Response

from server.map_data import empty_set
from server.workouts.models import ExerciseSession, Set
from server.workouts.set_serializers import SetDetailsSerializer, EditSetSerializer


# Sets
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
