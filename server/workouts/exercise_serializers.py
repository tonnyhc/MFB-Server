from rest_framework import serializers

from server.workouts.models import Exercise, ExerciseSession
from server.workouts.set_serializers import SetDetailsSerializer


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


class ExerciseDetailsSerializer(BaseExerciseSerializer):
    class Meta(BaseExerciseSerializer.Meta):
        fields = BaseExerciseSerializer.Meta.fields

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Customize targeted_muscle_groups to include names instead of ids
        targeted_muscle_groups = instance.targeted_muscle_groups.all()
        representation['targeted_muscle_groups'] = [group.name for group in targeted_muscle_groups]
        return representation


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


class CreateExerciseSerializer(BaseExerciseSerializer):
    class Meta(BaseExerciseSerializer.Meta):
        fields = BaseExerciseSerializer.Meta.fields
