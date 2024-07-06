from rest_framework import serializers

from server.profiles.serializers import BaseProfileSerializer
from server.utils import transform_timestamp
from server.workouts.exercise_serializers import ExerciseSessionSerializerNameOnly, ExerciseSessionDetailsSerializer, \
    BaseSupersetSessionSerializer
from server.workouts.models import WorkoutPlan, WorkoutSession, MuscleGroup
from server.workouts.utils import get_serialized_exercises


class BaseWorkoutSessionSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutSession
        fields = ('name', 'id', 'total_exercises', 'total_sets', 'total_weight_volume', 'is_published', 'created_at',)

    @staticmethod
    def get_created_at(obj):
        return transform_timestamp(str(obj.created_at))


# old was BaseWorkoutSerializer
class WorkoutDetailsSerializer(BaseWorkoutSessionSerializer):
    exercises = serializers.SerializerMethodField()

    class Meta(BaseWorkoutSessionSerializer.Meta):
        fields = (*BaseWorkoutSessionSerializer.Meta.fields, 'exercises')

    def get_exercises(self, obj):
        return get_serialized_exercises(obj)


class WorkoutSessionDetailsSerializer(BaseWorkoutSessionSerializer):
    exercises = serializers.SerializerMethodField()
    exercise_serializer = ExerciseSessionDetailsSerializer
    superset_serializer = BaseSupersetSessionSerializer

    class Meta(BaseWorkoutSessionSerializer.Meta):
        fields = BaseWorkoutSessionSerializer.Meta.fields + ('exercises',)

    def get_exercises(self, obj):
        exercises = []
        for exercise in obj.exercises.all():
            exercise_type = exercise.content_type.model
            exercise_instance = exercise.content_object
            if exercise_type == 'exercisesession':
                exercises.append(self.exercise_serializer(exercise_instance).data)
            elif exercise_type == 'supersetsession':
                exercises.append(self.superset_serializer(exercise_instance).data)
        return exercises


class BaseRoutineSerializer(serializers.ModelSerializer):
    created_by = BaseProfileSerializer()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutPlan
        fields = ("name", "id", "total_workouts", "workouts", "created_by", 'created_at')

    @staticmethod
    def get_created_at(obj):
        return transform_timestamp(str(obj.created_at))


class WorkoutPlanCreationSerializer(BaseRoutineSerializer):
    class Meta(BaseRoutineSerializer.Meta):
        fields = BaseRoutineSerializer.Meta.fields


class RoutineDetailsSerializer(BaseRoutineSerializer):
    workouts = WorkoutDetailsSerializer(many=True)

    class Meta(BaseRoutineSerializer.Meta):
        fields = BaseRoutineSerializer.Meta.fields + ('workouts',)


class RoutinesListSerializer(BaseRoutineSerializer):
    is_active = serializers.SerializerMethodField()

    class Meta(BaseRoutineSerializer.Meta):
        fields = BaseRoutineSerializer.Meta.fields + ('is_active',)

    def get_is_active(self, obj):
        request = self.context.get('request')
        profile = request.user.profile
        profile_active_routine = profile.activeroutine_set.first()
        return obj == profile_active_routine


class WorkoutPlanDetailsSerializer(BaseRoutineSerializer):
    workouts = WorkoutDetailsSerializer(many=True)

    class Meta(BaseRoutineSerializer.Meta):
        fields = (*BaseRoutineSerializer.Meta.fields, 'workouts')


class BaseMuscleGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = MuscleGroup
        fields = "__all__"
