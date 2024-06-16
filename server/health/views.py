from datetime import datetime

from rest_framework import generics as rest_generic_views, status, views
from rest_framework.response import Response

from server.health.models import Measures, ActivityChoicesMixin, FitnessGoalChoices
from server.health.serializers import EditMeasuresSerializer, EditFitnessSerializer
from server.utils import transform_timestamp, transform_timestamp_without_hour


class EditMeasures(rest_generic_views.UpdateAPIView):
    serializer_class = EditMeasuresSerializer

    def put(self, request, *args, **kwargs):
        dict_for_serializer = {}
        for key, value in request.data.items():
            print(value)
            dict_for_serializer[key] = float(value)

        serializer = self.serializer_class(instance=self.get_object(), data=dict_for_serializer, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_object(self):
        return self.request.user.profile.measures

    def get_queryset(self):
        return self.request.user.profile.measures
        # return Measures.objects.filter(profile=self.request.user.profile)


class FitnessActivityLevel(views.APIView):
    def get_queryset(self):
        return self.request.user.profile.fitness

    def put(self, request, *args, **kwargs):
        provided_activity = request.data.get('activity')
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

    def get(self, request):
        activity = self.request.user.profile.fitness.activity
        return Response({'activity': activity}, status=status.HTTP_200_OK)


class FitnessGoalView(views.APIView):

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

        fitness_instance = self.request.user.profile.fitness
        fitness_instance.goal = goal_enum_value
        fitness_instance.save()
        self.request.user.profile.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get(self, request):
        fitness_instance = self.request.user.profile.fitness
        goal = fitness_instance.goal
        goal_text = goal.split('.')[-1]
        return Response({
            'goal': goal_text,
        }, status=status.HTTP_200_OK)

# TODO: For delete
# class ProfileGoalView(views.APIView):
#     def get(self, request, *args, **kwargs):
#         profile = request.user.profile
#         fitness = profile.fitness
#         goal = fitness.goal
#         goal_text = goal.split('.')[-1]
#
#         return Response(goal_text, status=status.HTTP_200_OK)


class ProfileWeightView(views.APIView):
    def get(self, request):
        profile = self.request.user.profile
        measures = profile.measures
        weight = measures.weight
        weight_logs = [{'weight': log.weight, 'date': transform_timestamp_without_hour(str(log.history_date))} for log
                       in measures.history.all()]

        sorted_logs = sorted(weight_logs, key=lambda x: x['date'], reverse=True)

        # Get the date of the last entry
        last_entry_date = sorted_logs[0]['date'] if sorted_logs else None

        if last_entry_date:
            # Convert last entry date to datetime object
            last_entry_date = datetime.strptime(last_entry_date, '%d %b %Y')

            # Calculate time elapsed since last entry
            time_elapsed = datetime.now() - last_entry_date

            # Format time elapsed in a human-readable format
            if time_elapsed.days == 0:
                last_weigh_in = "Today"
            elif time_elapsed.days == 1:
                last_weigh_in = "Yesterday"
            else:
                last_weigh_in = f"{time_elapsed.days} days ago"
        else:
            last_weigh_in = None

        return_dict = {
            'last_weigh_in': last_weigh_in,
            'weight': weight,
            'logs': weight_logs
        }
        return Response(return_dict, status=status.HTTP_200_OK)

    def put(self, request):
        profile = self.request.user.profile
        new_weight = request.data.get('weight')
        measures = profile.measures
        if not new_weight:
            return Response("Weight is required", status=status.HTTP_400_BAD_REQUEST)
        measures.weight = float(new_weight)
        measures.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileHeightView(views.APIView):
    def get(self, request):
        profile = request.user.profile
        measures = profile.measures
        height = measures.height

        return Response({'height': height}, status=status.HTTP_200_OK)

    def put(self, request):
        profile = request.user.profile
        new_height = request.data.get('height')

        measures = profile.measures
        if not new_height:
            return Response("Height is required", status=status.HTTP_400_BAD_REQUEST)
        measures.height = int(new_height)
        measures.save()
        profile.save()
        print(measures.height)
        return Response(status=status.HTTP_204_NO_CONTENT)
