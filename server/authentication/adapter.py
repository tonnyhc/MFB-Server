from allauth.account.utils import user_email, user_field
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from server.cloudinary import upload_to_cloudinary
from server.profiles.models import Profile
from server.tasks import upload_profile_picture_to_cloudinary_and_save_to_profile


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = sociallogin.user
        user_email(user, data.get('email') or "")
        user_field(user, 'username', data.get('username') or data.get("email").split("@")[0])

        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        extra_data = sociallogin.account.extra_data
        full_name = extra_data.get('name')
        profile = Profile.objects.create_profile(user=user)
        profile_picture_url = extra_data.get('picture')

        upload_profile_picture_to_cloudinary_and_save_to_profile.delay(profile_picture_url, profile.pk)

        profile.full_name = full_name
        profile.save()
        return user
