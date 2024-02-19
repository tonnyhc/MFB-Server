from rest_framework import serializers

from server.health.models import Measures, Fitness


class BaseMeasuresSerializer(serializers.ModelSerializer):
    class Meta:
        model = Measures
        fields = "__all__"

class BaseFitnessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fitness
        fields = "__all__"

class EditMeasuresSerializer(BaseMeasuresSerializer):
    weight = serializers.CharField(allow_blank=False, allow_null=False)
    height = serializers.CharField(allow_blank=False, allow_null=False)
    class Meta(BaseMeasuresSerializer.Meta):
        # model = Measures
        fields = ('weight', 'height')


class EditFitnessSerializer(serializers.ModelSerializer):
    activity = serializers.CharField(allow_blank=False, allow_null=False)
    goal = serializers.CharField(allow_blank=False, allow_null=False)
    class Meta(BaseFitnessSerializer.Meta):
        fields = ('activity', 'goal')
