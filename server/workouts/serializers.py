from rest_framework import serializers

from server.profiles.serializers import BaseProfileSerializer
from server.utils import transform_timestamp
from server.workouts.models import WorkoutPlan, Exercise, WorkoutSession, ExerciseSession, Set, MuscleGroup


class BaseSetSerializer(serializers.ModelSerializer):

    class Meta:
        model = Set
        fields = "__all__"

class EditSetSerializer(BaseSetSerializer):
    class Meta(BaseSetSerializer.Meta):
        fields = BaseSetSerializer.Meta.fields


class SetDetailsSerializer(BaseSetSerializer):
    minReps = serializers.SerializerMethodField()
    maxReps = serializers.SerializerMethodField()
    failure = serializers.SerializerMethodField()

    class Meta(BaseSetSerializer.Meta):
        fields = ('reps', 'weight', 'minReps', 'maxReps', 'failure', 'bodyweight', 'set_index', 'id')

    def get_minReps(self, obj):
        return obj.min_reps

    def get_maxReps(self, obj):
        return obj.max_reps

    def get_failure(self, obj):
        return obj.to_failure


class BaseExerciseSerializer(serializers.ModelSerializer):
    cover_photo = serializers.SerializerMethodField()
    video_tutorial = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = ('id', 'name', 'cover_photo', 'targeted_muscle_groups',
                  'information', 'video_tutorial', 'tips',
                  'created_by', 'created_at', 'is_published')

    def get_cover_photo(self, obj):
        if obj.cover_photo:
            return obj.cover_photo.url
        return None

    def get_video_tutorial(self, obj):
        if obj.video_tutorial:
            return obj.video_tutorial.url
        return None
    # class Meta:
    #     model = Exercise
    #     fields = '__all__'

class BaseExerciseSessionSerializer(serializers.ModelSerializer):
    exercise = BaseExerciseSerializer()

    class Meta:
        model = ExerciseSession
        fields = "__all__"


class ExerciseSessionDetailsSerializer(BaseExerciseSessionSerializer):
    sets = SetDetailsSerializer(many=True)

    class Meta(BaseExerciseSessionSerializer.Meta):
        fields = BaseExerciseSessionSerializer.Meta.fields


class ExerciseSessionSerializerNameOnly(BaseExerciseSessionSerializer):
    name = serializers.SerializerMethodField()

    class Meta(BaseExerciseSessionSerializer.Meta):
        fields = ('name',)

    def get_name(self, obj):
        return obj.exercise.name


class BaseWorkoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutSession
        fields = ('id', 'created_at', "name", 'total_exercises', "total_sets", "total_weight_volume", "is_published",
                  'created_by', 'exercises')


class WorkoutDetailsSerializer(BaseWorkoutSerializer):
    exercises = ExerciseSessionSerializerNameOnly(many=True)

    class Meta(BaseWorkoutSerializer.Meta):
        fields = BaseWorkoutSerializer.Meta.fields


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


class CreateExerciseSerializer(BaseExerciseSerializer):
    class Meta(BaseExerciseSerializer.Meta):
        fields = BaseExerciseSerializer.Meta.fields



class BaseMuscleGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = MuscleGroup
        fields = "__all__"