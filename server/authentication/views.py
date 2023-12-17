from django.conf import settings
from django.contrib.auth import get_user_model, login, authenticate
from rest_framework import generics as rest_generic_views, views as rest_views, status
from rest_framework.authtoken import views as authtoken_views
from rest_framework.authtoken import models as authtoken_models
from rest_framework.response import Response
from django.core.mail import send_mail

from server.authentication.serializers import LoginSerializer, RegisterSerializer
from server.profiles.models import Profile

UserModel = get_user_model()


class LoginView(authtoken_views.ObtainAuthToken):
    authentication_classes = ()
    permission_classes = ()
    serializer_class = LoginSerializer
    """This view requires CSRF_TOKEN"""

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = authtoken_models.Token.objects.get_or_create(user=user)

        send_mail(subject='Add an eye-catching subject',
                  message='Write an amazing message',
                  from_email=settings.EMAIL_HOST_USER,
                  recipient_list=['smokercho56@gmail.com'])
        return Response({
            # 'user_id': user.pk,
            # 'username': user.username,
            # 'email': user.email,
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
                'user_id': user.pk,
                'username': user.username,
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
