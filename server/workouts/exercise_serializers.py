from rest_framework import serializers

from server.workouts.models import Exercise, ExerciseSession, Rest, Set, Interval
from server.workouts.set_serializers import SetDetailsSerializer, RestDetailsSerializer, IntervalDetailsSerializer


class BaseExerciseSerializer(serializers.ModelSerializer):
    video_tutorial = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = ('id', 'name', 'targeted_muscle_groups',
                  'instructions', 'video_tutorial', 'tips_and_tricks',
                  'created_by', 'created_at', 'is_published', 'is_cardio', 'bodyweight')

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
        representation['created_by'] = instance.created_by.user.username if instance.created_by else None
        return representation


class BaseExerciseSessionSerializer(serializers.ModelSerializer):
    exercise = BaseExerciseSerializer()

    class Meta:
        model = ExerciseSession
        fields = "__all__"


class ExerciseSessionDetailsSerializer(BaseExerciseSessionSerializer):
    session_data = serializers.SerializerMethodField()

    class Meta(BaseExerciseSessionSerializer.Meta):
        fields = BaseExerciseSessionSerializer.Meta.fields

    def get_session_data(self, obj):
        exercise_session_items = obj.exercisesessionitem_set.all()
        final_list = []
        for instance in exercise_session_items:
            model_class = instance.content_type.model_class()
            if model_class == Rest:
                final_list.append(RestDetailsSerializer(instance.item).data)
            elif model_class == Set:
                final_list.append(SetDetailsSerializer(instance.item).data)
            elif model_class == Interval:
                final_list.append(IntervalDetailsSerializer(instance.item).data)

        return final_list


class ExerciseSessionSerializerNameOnly(BaseExerciseSessionSerializer):
    name = serializers.SerializerMethodField()

    class Meta(BaseExerciseSessionSerializer.Meta):
        fields = ('name',)

    def get_name(self, obj):
        return obj.exercise.name

class ExerciseSessionEditSerializer(serializers.Serializer):
    class Meta(BaseExerciseSessionSerializer.Meta):
        fields = ('sets',)


class CreateExerciseSerializer(BaseExerciseSerializer):
    class Meta(BaseExerciseSerializer.Meta):
        fields = BaseExerciseSerializer.Meta.fields
