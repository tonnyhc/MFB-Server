import re

from allauth.account.models import EmailAddress
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.contrib.auth import get_user_model, login, authenticate
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework import generics as rest_generic_views, views as rest_views, status
from rest_framework.authtoken import views as authtoken_views
from rest_framework.authtoken import models as authtoken_models
from rest_framework.response import Response

from server.authentication.models import ConfirmationCode
from server.authentication.serializers import LoginSerializer, RegisterSerializer, \
    ConfirmVerificationCodeForPasswordResetSerializer, ResetPasswordSerializer, ChangePasswordSerializer
# from server.authentication.utils import send_confirmation_code_forgotten_password
from server.profiles.models import Profile
from server.authentication.tasks import send_confirmation_code_for_register, send_confirmation_code_forgotten_password

# from server.profiles.models import Profile

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
            'is_verified': user.is_verified,
            'key': token.key,
        })


class RegisterView(rest_generic_views.CreateAPIView):
    permission_classes = []
    authentication_classes = [ModelBackend]
    queryset = UserModel.objects.all()
    serializer_class = RegisterSerializer

    # TODO: Write some tests
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].lower()
        username = serializer.validated_data['username'].lower()

        password = request.data.get('password')
        data_for_serializer = {
            'email': email,
            'username': username,
            'password': password,
            'is_verified': False,
        }

        serializer = self.serializer_class(data=data_for_serializer, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # comented later
        Profile.objects.create_profile(user=user)
        EmailAddress.objects.create(user=user, email=email, verified=False, primary=True)

        if user:
            # added lated
            authenticated_user = authenticate(request, username=user.email, password=password)
            if authenticated_user:

                login(request, authenticated_user)
                token, created = authtoken_models.Token.objects.get_or_create(user=user)
                send_confirmation_code_for_register.delay(authenticated_user.pk)
                return Response({
                    'key': token.key,
                    'is_verified': False
                }, status=status.HTTP_201_CREATED)
            else:
                return Response("Invalid credentials", status=status.HTTP_400_BAD_REQUEST)
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
            if user.is_verified:
                return Response("User already verified", status=status.HTTP_400_BAD_REQUEST)
            send_confirmation_code_for_register.delay(user.pk)
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

        send_confirmation_code_forgotten_password.delay(user.pk)
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
            confirmation = ConfirmationCode.objects.filter(user=user, code=code, type="ForgottenPassword").get()
            user.set_password(password)
            user.save()

            confirmation.delete()
            return Response('Password reset successfully', status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response('A problem occurred', status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(rest_views.APIView):
    serializer_class = ChangePasswordSerializer

    def put(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = request.data.get('password')
        new_password = request.data.get('new_password')
        user = request.user
        if not user.check_password(raw_password=password):
            return Response('Wrong password', status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            return Response(e.messages, status=status.HTTP_400_BAD_REQUEST)
        else:
            user.set_password(new_password)
            user.save()
            return Response('Password changed successfully', status=status.HTTP_204_NO_CONTENT)


class VerifyAuthTokenAndGetUserDataView(rest_views.APIView):

    def get(self, request):
        token = authtoken_models.Token.objects.get_or_create(user=request.user)[0]

        return Response({
            'user_id': self.request.user.pk,
            'email': self.request.user.email,
            'is_verified': self.request.user.is_verified,
            'token': token.key,
        }, status=status.HTTP_200_OK)


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = "http://127.0.0.1:8000/accounts/google/login/callback/"
    client_class = OAuth2Client
