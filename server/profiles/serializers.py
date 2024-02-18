from rest_framework import serializers

from server.profiles.models import Profile


class BaseProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = "__all__"


class ProfileEditSerializer(BaseProfileSerializer):
    class Meta(BaseProfileSerializer.Meta):
        fields = ('full_name', 'birthday', 'gender')