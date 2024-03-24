from django.urls import path, include

from server.profiles.views import LoggedInProfileDetailsView, ProfileEditView, ProfileSetupFullNameView, \
    ProfileSetupGenderView, ProfileBirthDaySetupView

urlpatterns = [
    path('user-profile/', LoggedInProfileDetailsView.as_view(), name='logged in profile details'),
    path('setup/', include([
        path('full-name/', ProfileSetupFullNameView.as_view(), name='setup full name'),
        path('gender/', ProfileSetupGenderView.as_view(), name='setup gender'),
        path('birthday/', ProfileBirthDaySetupView.as_view(), name='setup birthday')
    ])),
    path('edit/', ProfileEditView.as_view(), name='edit profile'),
]
