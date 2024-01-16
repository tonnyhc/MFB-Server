from rest_framework import serializers

from server.profiles.serializers import BaseProfileSerializer
from server.utils import transform_timestamp
from server.workouts.models import WorkoutPlan, Exercise, WorkoutSession


class BaseWorkoutSessionSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    class Meta:
        model = WorkoutSession
        fields = "__all__"
    @staticmethod
    def get_created_at(obj):
        return transform_timestamp(str(obj.created_at))

class BaseWorkoutPlanSerializer(serializers.ModelSerializer):
    created_by = BaseProfileSerializer()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutPlan
        fields = "__all__"

    @staticmethod
    def get_created_at(obj):
        return transform_timestamp(str(obj.created_at))


class WorkoutPlanCreationSerializer(BaseWorkoutPlanSerializer):
    class Meta(BaseWorkoutPlanSerializer.Meta):
        fields = BaseWorkoutPlanSerializer.Meta.fields


class WorkoutPlanDetailsSerializer(BaseWorkoutPlanSerializer):
    workouts = BaseWorkoutSessionSerializer(many=True)

    class Meta(BaseWorkoutPlanSerializer.Meta):
        fields = BaseWorkoutPlanSerializer.Meta.fields


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = '__all__'
