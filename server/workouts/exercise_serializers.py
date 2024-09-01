from rest_framework import serializers

from server.workouts.models import CustomExercise
from server.workouts.set_serializers import SetDetailsSerializer, RestDetailsSerializer, IntervalDetailsSerializer


class CustomExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomExercise
        # fields = '__all__'
        exclude = ['created_by', 'created_at']


class BaseExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        from server.workouts.models import Exercise
        model = Exercise
        fields = "__all__"


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
        from server.workouts.models import ExerciseSession
        model = ExerciseSession
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['session_type'] = 'exercise'
        return representation


class ExerciseSessionDetailsSerializer(BaseExerciseSessionSerializer):
    session_data = serializers.SerializerMethodField()

    class Meta(BaseExerciseSessionSerializer.Meta):
        fields = BaseExerciseSessionSerializer.Meta.fields

    def get_session_data(self, obj):
        from server.workouts.models import Rest, Set, Interval
        exercise_session_items = obj.exercisesessionitem_set.all()
        final_list = []
        for instance in exercise_session_items:
            model_class = instance.content_type.model_class()
            if model_class == Rest:
                final_list.append(
                    {
                        "id": instance.item.pk,
                        "type": "rest",
                        "data": RestDetailsSerializer(instance.item).data,
                        "last": None}
                )
            elif model_class == Set:
                final_list.append(
                    {
                        "id": instance.item.pk,
                        "type": "set",
                        "data": SetDetailsSerializer(instance.item).data,
                        "last": SetDetailsSerializer(
                            instance.item.history.last()).data if instance.item.history.last() else None
                    })
            elif model_class == Interval:
                final_list.append(
                    {
                        "id": instance.item.pk,
                        "type": "interval",
                        "data": IntervalDetailsSerializer(instance.item).data,
                        "last": None
                    })

        return final_list


class ExerciseSessionSerializerNameOnly(BaseExerciseSessionSerializer):
    name = serializers.SerializerMethodField()
    sets_count = serializers.SerializerMethodField()

    class Meta(BaseExerciseSessionSerializer.Meta):
        fields = ('name', 'id', 'sets_count')

    def get_sets_count(self, obj):
        sets = obj.exercisesessionitem_set.all()
        return sets.count()

    def get_name(self, obj):
        return obj.exercise.name


class ExerciseSessionEditSerializer(serializers.Serializer):
    class Meta(BaseExerciseSessionSerializer.Meta):
        fields = ('sets',)


class CreateCustomExerciseSerializer(CustomExerciseSerializer):
    pass


# superset
class BaseSupersetSessionSerializer(serializers.ModelSerializer):
    exercises = ExerciseSessionDetailsSerializer(many=True)

    class Meta:
        from server.workouts.models import SupersetSession
        model = SupersetSession
        fields = ('id', 'created_by', 'created_at', 'exercises', 'notes')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['session_type'] = 'superset'
        return representation


class SupersetSessionSerializerNameOnly(BaseSupersetSessionSerializer):
    exercises = ExerciseSessionSerializerNameOnly(many=True)

    class Meta:
        from server.workouts.models import SupersetSession
        model = SupersetSession
        fields = ('id', 'exercises')
