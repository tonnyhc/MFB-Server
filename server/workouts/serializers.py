from rest_framework import serializers

from server.workouts.models import WorkoutPlan, Exercise


class WorkoutPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutPlan
        exclude = ('created_at',)


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = '__all__'