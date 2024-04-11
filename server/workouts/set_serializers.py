from rest_framework import serializers

from server.workouts.models import Set


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

