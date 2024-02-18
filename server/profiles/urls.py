from django.urls import path

from server.profiles.views import LoggedInProfileDetailsView, ProfileEditView

urlpatterns = [
    path('user-profile/', LoggedInProfileDetailsView.as_view(), name='logged in profile details'),
    path('edit/', ProfileEditView.as_view(), name='edit profile'),
]
