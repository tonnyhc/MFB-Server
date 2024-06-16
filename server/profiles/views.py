from cloudinary import uploader
from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.utils import timezone
import base64
from rest_framework import generics as rest_generic_views, status, views
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from server.models_utils import MAX_LEN_PROFILE_FULL_NAME, MAX_LEN_ACCOUNT_USERNAME, MAX_LEN_PROFILE_BIO
from server.profiles.models import Profile
from server.profiles.serializers import BaseProfileSerializer, ProfileEditSerializer
from server.profiles.tasks import upload_profile_picture_to_cloudinary_and_save_to_profile

UserModel = get_user_model()


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


class ProfileSetupFullNameView(rest_generic_views.UpdateAPIView):
    def put(self, request, *args, **kwargs):
        profile_instance = self.get_queryset()
        data = request.data
        if not profile_instance:
            return Response("An unexpected error occurred!", status=status.HTTP_400_BAD_REQUEST)
        if not data:
            return Response("Full name is required", status=status.HTTP_400_BAD_REQUEST)
        profile_instance.full_name = data
        profile_instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user).first()


class ProfileSetupGenderView(views.APIView):
    def put(self, request, *args, **kwargs):
        profile_instance = self.request.user.profile
        data = request.data
        if not profile_instance:
            return Response("An unexpected error occurred!", status=status.HTTP_400_BAD_REQUEST)
        if not data:
            return Response("Gender is required", status=status.HTTP_400_BAD_REQUEST)
        profile_instance.gender = data
        profile_instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get(self, request):
        gender = self.request.user.profile.gender
        return Response({"gender": gender}, status=status.HTTP_200_OK)


# class ProfileBirthDaySetupView(rest_generic_views.UpdateAPIView):
#     def put(self, request, *args, **kwargs):
#         profile_instance = self.get_queryset()
#         data = request.data
#         if not profile_instance:
#             return Response("An unexpected error occurred!", status=status.HTTP_400_BAD_REQUEST)
#         if not data:
#             return Response("Birthdate is required", status=status.HTTP_400_BAD_REQUEST)
#
#         # date_string = "2024-03-07"
#         date_string = request.data
#         print(request.data)
#         # Convert the string to a datetime object
#         date_object = datetime.strptime(date_string, "%Y-%m-%d")
#
#         # Convert the datetime object to a timezone-aware datetime object
#         # You can skip this step if you don't need timezone awareness
#         date_object_aware = timezone.make_aware(date_object)
#
#         profile_instance.birthday = date_object_aware
#
#         profile_instance.save()
#         return Response(status=status.HTTP_204_NO_CONTENT)
#
#     def get_queryset(self):
#         return Profile.objects.filter(user=self.request.user).first()


class FullnameAndFullnameValidatorsView(views.APIView):

    def get(self, request):
        return_dict = {
            'full_name': self.request.user.profile.full_name,
            'max_length_full_name': MAX_LEN_PROFILE_FULL_NAME
        }
        return Response(return_dict, status=status.HTTP_200_OK)

    def put(self, request):
        full_name = request.data.get('full_name')

        profile = request.user.profile
        profile.full_name = full_name
        profile.save()
        response = self.get(request)
        return Response(response.data, status=status.HTTP_200_OK)


class UsernameAndValidatorsView(views.APIView):
    def get(self, request):
        return_dict = {
            'username': self.request.user.username,
            'max_length_username': MAX_LEN_ACCOUNT_USERNAME
        }
        return Response(return_dict, status=status.HTTP_200_OK)

    def put(self, request):
        new_username = request.data.get('username')
        try:
            existing_user = UserModel.objects.get(username=new_username)
            if existing_user == request.user:
                return Response(self.get(request).data, status=status.HTTP_200_OK)
            return Response("This username isn't available. Please try another.", status=status.HTTP_400_BAD_REQUEST)
        except UserModel.DoesNotExist:
            user = request.user
            user.username = new_username
            user.save()
            response = self.get(request)
            return Response(response.data, status=status.HTTP_200_OK)


class BioAndValidatorsView(views.APIView):

    def get(self, request):
        return_dict = {
            'bio': self.request.user.profile.bio,
            'max_length_bio': MAX_LEN_PROFILE_BIO
        }
        return Response(return_dict, status=status.HTTP_200_OK)

    def put(self, request):
        bio = request.data.get('bio')
        profile = request.user.profile
        profile.bio = bio
        profile.save()
        response = self.get(request)
        return Response(response.data, status=status.HTTP_200_OK)


class BirthdayAndValidatorsView(views.APIView):

    def get(self, request):
        return_dict = {
            'birthday': self.request.user.profile.birthday,
        }
        return Response(return_dict, status=status.HTTP_200_OK)

    def put(self, request):
        profile_instance = self.request.user.profile
        data = request.data

        if not profile_instance:
            return Response("An unexpected error occurred!", status=status.HTTP_400_BAD_REQUEST)
        if not data:
            return Response("Birthdate is required", status=status.HTTP_400_BAD_REQUEST)

        profile_instance.birthday = request.data
        profile_instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfilePictureView(views.APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = []

    def put(self, request):
        new_picture = request.FILES.get('profile_picture')
        profile = self.request.user.profile
        if not new_picture:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # Coding the image to a base64
        encoded_picture = base64.b64encode(new_picture.read()).decode('utf-8')
        # sending the encoded base64 to celery
        upload_profile_picture_to_cloudinary_and_save_to_profile.delay(encoded_picture, profile.pk)
        return Response(status=status.HTTP_202_ACCEPTED)
        # return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request):
        profile = request.user.profile
        picture = profile.picture
        if picture:
            public_id = picture.public_id
            uploader.destroy(public_id)
            profile.picture = None
            profile.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):

        return Response({
            'profile_picture': self.request.user.profile.picture.url if self.request.user.profile.picture else ''
        })
