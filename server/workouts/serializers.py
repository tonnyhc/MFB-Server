from rest_framework import serializers

from server.profiles.serializers import BaseProfileSerializer
from server.utils import transform_timestamp
from server.workouts.exercise_serializers import ExerciseSessionSerializerNameOnly, ExerciseSessionDetailsSerializer
from server.workouts.models import WorkoutPlan, WorkoutSession, MuscleGroup



class BaseWorkoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutSession
        fields = ('id', 'created_at', "name", 'total_exercises', "total_sets", "total_weight_volume", "is_published",
                  'created_by', 'exercises')


class WorkoutDetailsSerializer(BaseWorkoutSerializer):
    exercises = ExerciseSessionSerializerNameOnly(many=True)

    class Meta(BaseWorkoutSerializer.Meta):
        fields = BaseWorkoutSerializer.Meta.fields


class WorkoutSessionEditSerializer(BaseWorkoutSerializer):
    exercises = ExerciseSessionDetailsSerializer(many=True)
    class Meta(BaseWorkoutSerializer.Meta):
        fields = ("name", "exercises", )

class BaseWorkoutSessionSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutSession
        fields = "__all__"

    @staticmethod
    def get_created_at(obj):
        return transform_timestamp(str(obj.created_at))


class WorkoutSessionDetailsSerializer(BaseWorkoutSessionSerializer):
    exercises = ExerciseSessionDetailsSerializer(many=True)

    class Meta(BaseWorkoutSessionSerializer.Meta):
        fields = BaseWorkoutSessionSerializer.Meta.fields


class BaseWorkoutPlanSerializer(serializers.ModelSerializer):
    created_by = BaseProfileSerializer()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutPlan
        fields = ("name", "id", "total_workouts", "workouts", "created_by", 'created_at')

    @staticmethod
    def get_created_at(obj):
        return transform_timestamp(str(obj.created_at))


class RoutinesListSerializer(BaseWorkoutPlanSerializer):
    is_active = serializers.SerializerMethodField()
    class Meta(BaseWorkoutPlanSerializer.Meta):
        fields = BaseWorkoutPlanSerializer.Meta.fields + ('is_active',)

    def get_is_active(self, obj):
        request = self.context.get('request')
        profile = request.user.profile
        profile_active_routine = profile.activeroutine_set.first()
        return obj == profile_active_routine


class WorkoutPlanCreationSerializer(BaseWorkoutPlanSerializer):
    class Meta(BaseWorkoutPlanSerializer.Meta):
        fields = BaseWorkoutPlanSerializer.Meta.fields


class WorkoutPlanDetailsSerializer(BaseWorkoutPlanSerializer):
    workouts = WorkoutDetailsSerializer(many=True)

    class Meta(BaseWorkoutPlanSerializer.Meta):
        fields = (*BaseWorkoutPlanSerializer.Meta.fields, 'workouts')

    # def get_workouts(self, obj):
    #     workout_serializer = WorkoutDetailsSerializer(many=True)
    #     return workout_serializer(obj.workouts)





class BaseMuscleGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = MuscleGroup
        fields = "__all__"