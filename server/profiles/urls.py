from django.urls import path, include

from server.profiles.views import LoggedInProfileDetailsView, ProfileEditView, ProfileSetupFullNameView, \
    ProfileSetupGenderView, ProfileBirthDaySetupView, FullnameAndFullnameValidatorsView, UsernameAndValidatorsView, \
    BioAndValidatorsView, BirthdayAndValidatorsView, ProfilePictureView

urlpatterns = [
    path('full_name/', FullnameAndFullnameValidatorsView.as_view(), name='profile full name'),
    path('username/', UsernameAndValidatorsView.as_view(), name='account username'),
    path('bio/', BioAndValidatorsView.as_view(), name='profile bio'),
    path('birthday/', BirthdayAndValidatorsView.as_view(), name='profile birthday'),
    path('profile-picture/', ProfilePictureView.as_view(), name='profile picture'),
    path('user-profile/', LoggedInProfileDetailsView.as_view(), name='logged in profile details'),
    path('setup/', include([
        path('full-name/', ProfileSetupFullNameView.as_view(), name='setup full name'),
        path('gender/', ProfileSetupGenderView.as_view(), name='setup gender'),
        path('birthday/', ProfileBirthDaySetupView.as_view(), name='setup birthday')
    ])),
    path('edit/', ProfileEditView.as_view(), name='edit profile'),
]
