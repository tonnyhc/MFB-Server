from django.shortcuts import render
from rest_framework import generics as rest_generic_views, status
from rest_framework.response import Response

from server.profiles.models import Profile
from server.profiles.serializers import BaseProfileSerializer, ProfileEditSerializer


class LoggedInProfileDetailsView(rest_generic_views.RetrieveAPIView):
    serializer_class = BaseProfileSerializer

    def get(self, request, *args, **kwargs):
        try:
            profile = request.user.profile
            serialized_profile = self.serializer_class(profile)
            return Response(serialized_profile.data, status=status.HTTP_200_OK)

        except Profile.DoesNotExist:
            return Response({'An error occurred, please try again later!'}, status=status.HTTP_400_BAD_REQUEST)


class ProfileEditView(rest_generic_views.UpdateAPIView):
    serializer_class = ProfileEditSerializer

    def put(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = self.get_queryset().first()
        profile.full_name = serializer.validated_data['full_name']
        profile.gender = serializer.validated_data['gender']
        profile.birthday = serializer.validated_data['birthday']
        profile.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)
