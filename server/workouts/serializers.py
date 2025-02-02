from rest_framework import serializers

from server.profiles.serializers import BaseProfileSerializer
from server.utils import transform_timestamp
from server.workouts.exercise_serializers import ExerciseSessionSerializerNameOnly, ExerciseSessionDetailsSerializer, \
    BaseSupersetSessionSerializer
from server.workouts.models import WorkoutPlan, WorkoutSession, MuscleGroup, CustomExercise, WorkoutTemplate
from server.workouts.utils import get_serialized_exercises, serializer_exericses_for_session_or_template


class BaseWorkoutSessionSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutSession
        fields = ('name', 'id', 'total_exercises', 'total_sets', 'total_weight_volume', 'created_at',)

    @staticmethod
    def get_created_at(obj):
        return transform_timestamp(str(obj.created_at))


class CreateWorkoutTemplateSerializer(BaseWorkoutSessionSerializer):
    pass


class CustomExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomExercise
        fiels = "__all__"


class WorkoutListSerializer(BaseWorkoutSessionSerializer):
    exercises = serializers.SerializerMethodField()

    class Meta(BaseWorkoutSessionSerializer.Meta):
        fields = BaseWorkoutSessionSerializer.Meta.fields + ('exercises',)

    def get_exercises(self, obj):
        return get_serialized_exercises(obj)


class WorkoutTemplateListSerializer(serializers.ModelSerializer):
    exercises = serializers.SerializerMethodField()

    class Meta:
        fields = "__all__"
        model = WorkoutTemplate

    def get_exercises(self, obj):
        return get_serialized_exercises(obj)


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
        exercises_for_fn = obj.exercises.all()
        return serializer_exericses_for_session_or_template(exercises_for_fn,
                                                            exercise_serializer=self.exercise_serializer,
                                                            superset_serializer=self.superset_serializer)


class WorkoutTemplateSerializer(serializers.ModelSerializer):
    exercises = serializers.SerializerMethodField()
    exercise_serializer = ExerciseSessionDetailsSerializer
    superset_serializer = BaseSupersetSessionSerializer

    class Meta:
        model = WorkoutTemplate
        fields = "__all__"

    def get_exercises(self, obj):
        exercises_for_fn = obj.exercises.all()
        return serializer_exericses_for_session_or_template(exercises_for_fn,
                                                            exercise_serializer=self.exercise_serializer,
                                                            superset_serializer=self.superset_serializer)


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
    workouts = WorkoutDetailsSerializer(many=True)

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
