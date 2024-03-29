import re

from django.contrib.auth import get_user_model, login
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics as rest_generic_views, views as rest_views, status
from rest_framework.authtoken import views as authtoken_views
from rest_framework.authtoken import models as authtoken_models
from rest_framework.response import Response

from server.authentication.models import ConfirmationCode
from server.authentication.serializers import LoginSerializer, RegisterSerializer, \
    ConfirmVerificationCodeForPasswordResetSerializer, ResetPasswordSerializer
from server.authentication.utils import send_confirmation_code_forgotten_password, send_confirmation_code_for_register
from server.profiles.models import Profile

UserModel = get_user_model()


class LoginView(authtoken_views.ObtainAuthToken):
    authentication_classes = ()
    permission_classes = ()
    serializer_class = LoginSerializer
    """This view requires CSRF_TOKEN"""

    def post(self, request, *args, **kwargs):
        refactored_data = {
            **request.data,
            'email': request.data.get('email').lower() if request.data.get('email') else ""
        }
        serializer = self.serializer_class(data=refactored_data,
                                           context={'request': request})
        if not serializer.is_valid():
            return Response("Invalid email/password", status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        token, created = authtoken_models.Token.objects.get_or_create(user=user)

        return Response({
            # 'user_id': user.pk,
            # 'username': user.username,
            'email': user.email,
            'is_verified': user.is_verified,
            'token': token.key,
        })


class RegisterView(rest_generic_views.CreateAPIView):
    permission_classes = []
    authentication_classes = []
    queryset = UserModel.objects.all()
    serializer_class = RegisterSerializer

    # TODO: Write some tests
    def post(self, request, *args, **kwargs):
        username_to_lower_case = request.data.get('username').lower()

        email_to_lower_case = request.data.get('email').lower()
        password = request.data.get('password')
        data_for_serializer = {
            'email': email_to_lower_case,
            'username': username_to_lower_case,
            'password': password
        }

        serializer = self.serializer_class(data=data_for_serializer, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        Profile.objects.create_profile(user=user)

        if user:
            login(request, user)
            token, created = authtoken_models.Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                # 'user_id': user.pk,
                # 'username': user.username,
                'email': user.email,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(rest_views.APIView):
    def get(self, request):
        return self.__perform_logout(request)

    def post(self, request):
        return self.__perform_logout(request)

    @staticmethod
    def __perform_logout(request):
        try:
            request.user.auth_token.delete()
            return Response({
                'message': 'User signed out'
            }, status=status.HTTP_200_OK)
        except AttributeError as e:
            return Response({
                'message': "No signed in user, cant perform sign-out!"
            }, status=status.HTTP_400_BAD_REQUEST)


class ConfirmEmail(rest_views.APIView):

    def post(self, request, *args, **kwargs):
        code = request.data
        user = request.user

        if not user:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if not code:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        confirmation = UserModel.objects.confirm_email(user, code)
        if not confirmation:
            return Response("Wrong confirmation code", status=status.HTTP_400_BAD_REQUEST)
        return Response(
            "Email confirmed",
            status=status.HTTP_200_OK)


class ResentVerificationCode(rest_views.APIView):
    def get(self, request):
        try:
            user = request.user
            send_confirmation_code_for_register(user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response("An unexpected problem occurred.", status=status.HTTP_400_BAD_REQUEST)


class ForgottenPasswordView(rest_views.APIView):
    permission_classes = []
    authentication_classes = []
    regex = r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"

    def post(self, request):
        email_from_request_data = request.data
        email = ""
        if email_from_request_data:
            email = email_from_request_data.lower()

        if not email or not re.match(self.regex, email):
            return Response("Invalid email format", status=status.HTTP_400_BAD_REQUEST)
        try:
            user = UserModel.objects.filter(email=email).get()
        except ObjectDoesNotExist:
            return Response('This email is not associated to any profile', status=status.HTTP_400_BAD_REQUEST)

        send_confirmation_code_forgotten_password(user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConfirmVerificationCodeForPasswordReset(rest_views.APIView):
    permission_classes = []
    authentication_classes = []
    serializer_class = ConfirmVerificationCodeForPasswordResetSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email'].lower()
        code = serializer.validated_data['code']

        try:
            user = UserModel.objects.filter(email=email).get()
        except ObjectDoesNotExist:
            return Response('The email is not associated with any profile', status=status.HTTP_400_BAD_REQUEST)

        if ConfirmationCode.objects.filter(user=user, code=code, type="ForgottenPassword"):
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response("Invalid verification code", status=status.HTTP_400_BAD_REQUEST)


class RessetPasswordView(rest_views.APIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email'].lower()
        code = serializer.validated_data['code']
        password = serializer.validated_data['password']

        try:
            user = UserModel.objects.filter(email=email).get()
            confirmation = ConfirmationCode.objects.filter(user=user, code=code, type="ForgottenPassword")
            user.set_password(password)
            user.save()

            confirmation.delete()
            return Response('Password reset successfully', status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response('A problem occurred', status=status.HTTP_400_BAD_REQUEST)


class VerifyAuthTokenView(rest_views.APIView):

    def get(self, request):

        return Response(status=status.HTTP_204_NO_CONTENT)
