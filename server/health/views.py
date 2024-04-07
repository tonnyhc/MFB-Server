from rest_framework import generics as rest_generic_views, status
from rest_framework.response import Response

from server.health.models import Measures, ActivityChoicesMixin, FitnessGoalChoices
from server.health.serializers import EditMeasuresSerializer, EditFitnessSerializer


class EditMeasures(rest_generic_views.UpdateAPIView):
    serializer_class = EditMeasuresSerializer

    def put(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        measures = self.get_queryset()
        measures.weight = serializer.validated_data['weight']
        measures.height = serializer.validated_data['height']
        measures.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        return self.request.user.profile.measures_set.first()
        # return Measures.objects.filter(profile=self.request.user.profile)


class EditActivity(rest_generic_views.UpdateAPIView):
    def get_queryset(self):
        return self.request.user.profile.fitness_set.first()

    def put(self, request, *args, **kwargs):
        provided_activity = request.data
        if not provided_activity:
            return Response({'error': 'Activity field is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            activity_enum_value = ActivityChoicesMixin(provided_activity)
        except ValueError:
            return Response({'error': f'Invalid activity choice: {provided_activity}'},
                            status=status.HTTP_400_BAD_REQUEST)

        query = self.get_queryset()
        query.activity = provided_activity
        query.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EditGoal(rest_generic_views.UpdateAPIView):

    def put(self, request, *args, **kwargs):
        provided_goal = request.data
        print(provided_goal)
        if not provided_goal:
            return Response({'error': 'Fitness goal is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            goal_enum_value = FitnessGoalChoices(provided_goal)
        except ValueError:
            return Response({'error': f'Invalid goal choice: {provided_goal}'},
                            status=status.HTTP_400_BAD_REQUEST)

        query = self.get_queryset()
        print(goal_enum_value)
        query.goal = goal_enum_value
        query.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        return self.request.user.profile.fitness_set.first()
