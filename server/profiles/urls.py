from django.urls import path

from server.profiles.views import LoggedInProfileDetailsView

urlpatterns = [
    path('user-profile/', LoggedInProfileDetailsView.as_view(), name='logged in profile details'),
]
