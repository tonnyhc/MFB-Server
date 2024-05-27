from allauth.account.utils import user_email, user_field
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


from server.profiles.models import Profile


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = sociallogin.user
        user_email(user, data.get('email') or "")
        user_field(user, 'username', data.get('username') or data.get("email").split("@")[0])
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        Profile.objects.create(user=user)
        return user

