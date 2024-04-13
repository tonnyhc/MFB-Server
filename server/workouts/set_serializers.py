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
    class Meta(BaseSetSerializer.Meta):
        fields = ('reps', 'weight', 'min_reps', 'max_reps', 'to_failure', 'bodyweight', 'set_index', 'id')
