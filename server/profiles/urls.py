from django.urls import path

from server.profiles.views import LogedInProfileDetailsView

urlpatterns = [
    path('user-profile/', LogedInProfileDetailsView.as_view(), name='logged in profile details'),
]
