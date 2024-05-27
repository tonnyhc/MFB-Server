from django.urls import path, include

from server.authentication.views import RegisterView, LogoutView, LoginView, ConfirmEmail, ForgottenPasswordView, \
    ConfirmVerificationCodeForPasswordReset, RessetPasswordView, ResentVerificationCode, \
    VerifyAuthTokenAndGetUserDataView, \
    ChangePasswordView, GoogleLogin

urlpatterns = [
    path('login/', LoginView.as_view(), name='login view'),
    path('logout/', LogoutView.as_view(), name='logout view'),
    path('register/', RegisterView.as_view(), name='register view'),
    path('resend-confirmation/', ResentVerificationCode.as_view(), name='resend confirmation code'),
    path('verify-account/', ConfirmEmail.as_view(), name='verify account'),
    path('forgotten-password/', ForgottenPasswordView.as_view(), name='forgotten password'),
    path('forgotten-password/verify-code/', ConfirmVerificationCodeForPasswordReset.as_view(),
         name='forgotten password verify code'),
    path('forgotten-password/reset/', RessetPasswordView.as_view(), name='forgotten password reset'),
    path('verify-token/', VerifyAuthTokenAndGetUserDataView.as_view(), name='verify token'),
    path('change-password/', ChangePasswordView.as_view(), name='change password'),
    # social auth
    path('social/', include([
        path('google/', GoogleLogin.as_view(), name='google login')
    ]))
]
