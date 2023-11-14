from django.shortcuts import render
from rest_framework import generics as rest_generic_views, status
from rest_framework.response import Response

from server.profiles.models import Profile
from server.profiles.serializers import BaseProfileSerializer


class LogedInProfileDetailsView(rest_generic_views.RetrieveAPIView):
    serializer_class = BaseProfileSerializer
    def get(self, request, *args, **kwargs):
        try:
            profile = request.user.profile
            serialized_profile = self.serializer_class(profile)
            return Response(serialized_profile.data, status=status.HTTP_200_OK)

        except Profile.DoesNotExist:
            return Response({'An error occurred, please try again later!'}, status=status.HTTP_400_BAD_REQUEST)