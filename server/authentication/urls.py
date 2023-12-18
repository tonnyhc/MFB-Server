from django.urls import path

from server.authentication.views import RegisterView, LogoutView, LoginView, ConfirmEmail, ForgottenPasswordView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login view'),
    path('logout/', LogoutView.as_view(), name='logout view'),
    path('register/', RegisterView.as_view(), name='register view'),
    path('verify-account/', ConfirmEmail.as_view(), name='verify account'),
    path('forgotten-password/', ForgottenPasswordView.as_view(), name='forgotten password'),
]