from rest_framework import serializers

from server.profiles.models import Profile


class BaseProfileSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    picture = serializers.SerializerMethodField()
    class Meta:
        model = Profile
        fields = ('id', 'full_name', 'gender', 'birthday', 'bio', 'picture', 'user')

    def get_picture(self, obj):
        if not obj.picture:
            return 'https://res.cloudinary.com/dnb8qwwyi/image/upload/v1713645340/Default_pfp.svg_lovmuw.png'
        return obj.picture.url
    def get_user(self, obj):
        return obj.user.username


class ProfileEditSerializer(BaseProfileSerializer):
    class Meta(BaseProfileSerializer.Meta):
        fields = ('full_name', 'birthday', 'gender')
