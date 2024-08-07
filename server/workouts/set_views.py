from rest_framework import generics as rest_generic_views, status, views
from rest_framework.response import Response

from server.map_data import empty_set
from server.workouts.models import ExerciseSession, Set
from server.workouts.set_serializers import SetDetailsSerializer, EditSetSerializer
from server.workouts.utils import convert_str_to_float


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
    def delete(self, request, *args, **kwargs):
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

    def put(self, request, *args, **kwargs):
        set_id = kwargs.get('set_id')
        try:
            set_instance = self.queryset.get(id=set_id)
            data = request.data
            set_data = data.get('data')

            weight = set_data.get('weight')
            converted_weight = convert_str_to_float(weight)
            set_obj = {
                'reps': str(set_data.get('reps')),
                "weight": converted_weight,
                "max_reps": str(set_data.get('max_reps', set_instance.max_reps)),
                "min_reps": str(set_data.get('min_reps', set_instance.min_reps)),
                "to_failure": set_data.get('to_failure', set_instance.to_failure),
                "bodyweight": set_data.get('bodyweight', set_instance.bodyweight),
                'created_by': set_instance.created_by.pk
            }
            serializer = self.serializer_class(data=set_obj)
            serializer.is_valid(raise_exception=True)

            updated_instance = Set.edit_data(request, set_instance, set_obj)
            updated_instance.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Set.DoesNotExist:
            return Response('There was an error updating the set!', status=status.HTTP_400_BAD_REQUEST)
