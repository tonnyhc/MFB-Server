from rest_framework import serializers

from server.workouts.models import Set, Rest, Interval


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


class RestBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rest
        fields = "__all__"


class RestDetailsSerializer(RestBaseSerializer):
    class Meta(RestBaseSerializer.Meta):
        fields = ('minutes', 'seconds', 'id')


class BaseIntervalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interval
        fields = "__all__"


class IntervalDetailsSerializer(BaseIntervalSerializer):
    class Meta(BaseIntervalSerializer.Meta):
        fields = BaseIntervalSerializer.Meta.fields