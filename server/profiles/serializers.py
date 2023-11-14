from rest_framework import serializers

from server.profiles.models import Profile


class BaseProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = "__all__"