from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from server.authentication.models import ConfirmationCode
from server.profiles.models import Profile

UserModel = get_user_model()


class RegisterViewTests(APITestCase):
    def test_register_valid_user(self):
        url = '/authentication/register/'
        data = {
            'email': 'test@example.com',
            'username': 'test_user',
            'password': 'test_password',
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('user_id', response.data)
        self.assertEqual(response.data['email'], 'test@example.com')

        user = UserModel.objects.get(email='test@example.com')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_verified)  # when creating the user is_verified is false

        # Checking if the profile and the email are created and if not it will raise an error and the test will fail
        Profile.objects.get(user=user)
        EmailAddress.objects.get(user=user, email=user.email)

    def test_register_invalid_email(self):
        url = '/authentication/register/'
        data = {
            'email': '',  # Невалиден имейл
            'username': 'test_user',
            'password': 'test_password',
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_duplicate_email(self):
        # Creating an user that already exists
        existing_user = UserModel.objects.create_user(
            email='existing@example.com',
            username='existing_user',
            password='existing_password',
        )

        url = "/authentication/register/"
        data = {
            'email': 'existing@example.com',  # Email is taken
            'username': 'test_user',
            'password': 'test_password',
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)  # Checking for error including email in the error

    def test_register_dublicate_username(self):
        # Creating an user that already exists
        existing_user = UserModel.objects.create_user(
            email='existing@example.com',
            username='existing_user',
            password='existing_password',
        )

        url = "/authentication/register/"
        data = {
            'email': 'test@example.com',  # Email is taken
            'username': 'existing_user',
            'password': 'test_password',
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)  # Checking for error including username in the error

    def test_register_with_groups(self):
        # Създаване на група, която да се добави към потребителя
        group = Group.objects.create(name='Test Group')

        url = "/authentication/register/"  # Предполагам, че името на URL-то за регистрация е 'register'
        data = {
            'email': 'group@example.com',
            'username': 'group_user',
            'password': 'group_password',
            'groups': [group.id],  # Добавяне на групата към новия потребител
        }


class LoginViewApiTestCase(APITestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(email='test@example.com', password='test_password')

    def test_login_valid_credentials(self):
        url = "/authentication/login/"
        data = {
            'email': 'test@example.com',
            'password': 'test_password',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user_id', response.data)
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_login_invalid_credentials(self):
        url = "/authentication/login/"
        data = {
            'email': 'test@example.com',
            'password': 'wrong_password',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid email/password', response.data)

    def test_login_missing_email(self):
        url = "/authentication/login/"
        data = {
            'password': 'test_password',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid email/password', response.data)

    def test_login_missing_password(self):
        url = "/authentication/login/"
        data = {
            'email': 'test@example.com',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid email/password', response.data)

    def test_login_invalid_method(self):
        url = "/authentication/login/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_login_with_inactive_user(self):
        self.user.is_active = False
        self.user.save()

        url = "/authentication/login/"
        data = {
            'email': 'test@example.com',
            'password': 'test_password',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid email/password', response.data)

    def test_login_with_empty_email(self):
        url = "/authentication/login/"
        data = {
            'email': '',
            'password': 'test_password',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid email/password', response.data)

    def test_login_with_empty_password(self):
        url = "/authentication/login/"
        data = {
            'email': 'test@example.com',
            'password': '',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid email/password', response.data)


class LogoutViewApiTestCase(APITestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(email='test@example.com', password='test_password')
        login_url = '/authentication/login/'
        login_data = {
            'email': 'test@example.com',
            'password': 'test_password'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        self.token = login_response.data['token']

    def test_logout_post_request(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        url = "/authentication/logout/"
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('message'), 'User signed out')

    def test_logout_get_request(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        url = "/authentication/logout/"
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('message'), 'User signed out')

    def test_logout_without_token(self):
        url = "/authentication/logout/"
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'Authentication credentials were not provided.')

    def test_logout_with_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + 'invalid_token')
        url = "/authentication/logout/"
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'Invalid token.')


class ConfirmEmailViewApiTestCase(APITestCase):
    def setUp(self):
        # first we must register the user
        register_url = '/authentication/register/'
        register_data = {
            "username": "test",
            "email": "test@example.com",
            "password": "Test1234!"
        }
        response = self.client.post(register_url, register_data, format='json')
        # getting the user's verification code from the base
        self.user = UserModel.objects.get(email="test@example.com")
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + response.data.get('token'))
        confirmation_code_instance = ConfirmationCode.objects.get(user=self.user, type='AccountVerification')
        self.confirmation_code = confirmation_code_instance.code
        self.url = '/authentication/verify-account/'  # Adjust the URL name as per your URL configuration

    def test_confirm_email_with_valid_code(self):
        response = self.client.post(self.url, self.confirmation_code, format='json')
        self.assertEqual(response.data, "Email confirmed")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_confirm_email_with_invalid_code(self):
        response = self.client.post(self.url, "invalid", format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "Wrong confirmation code")


class ForgottenPasswordViewTests(APITestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(email='test@example.com', password='test_password')
        self.url = '/authentication/forgotten-password/'

    def test_forgotten_password_success(self):
        data = 'test@example.com'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Add assertions to check for any side effects, such as the presence of an email confirmation record, if applicable

    def test_forgotten_password_invalid_email_format(self):
        data = 'invalid-email'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "Invalid email format")

    def test_forgotten_password_non_existent_email(self):
        data = 'nonexistent@example.com'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, 'This email is not associated to any profile')

    def test_forgotten_password_missing_email(self):
        data = {}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "Invalid email format")


class ConfirmVerificationCodeForPasswordResetTests(APITestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(email='test@example.com', password='test_password')
        self.confirmation_code = ConfirmationCode.objects.create(user=self.user, code='12345', type='ForgottenPassword')
        self.url = '/authentication/forgotten-password/verify-code/'  # Adjust the URL name as per your URL configuration

    def test_confirm_verification_code_success(self):
        data = {
            'email': 'test@example.com',
            'code': '12345'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_confirm_verification_code_invalid_code(self):
        data = {
            'email': 'test@example.com',
            'code': 'invalid_code'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "Invalid verification code")

    def test_confirm_verification_code_non_existent_email(self):
        data = {
            'email': 'nonexistent@example.com',
            'code': '123456'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, 'The email is not associated with any profile')

    def test_confirm_verification_code_missing_fields(self):
        data = {
            'email': 'test@example.com'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ResetPasswordViewTests(APITestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(email='test@example.com', password='old_password')
        self.confirmation_code = ConfirmationCode.objects.create(user=self.user, code='12345', type='ForgottenPassword')
        self.url = "/authentication/forgotten-password/reset/"

    def test_reset_password_success(self):
        data = {
            'email': 'test@example.com',
            'code': '12345',
            'password': 'new_password',
            "re_pass": "new_password"
        }
        response = self.client.post(self.url, data, format='json')
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(UserModel.objects.get(email='test@example.com').check_password('new_password'), True)
        self.assertEqual(
            ConfirmationCode.objects.filter(user=self.user, code='12345', type='ForgottenPassword').exists(), False)

    def test_reset_password_invalid_code(self):
        data = {
            'email': 'test@example.com',
            'code': 'invalid_code',
            'password': 'new_password',
            "re_pass": "new_password"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, "A problem occurred")

    def test_reset_password_non_existent_email(self):
        data = {
            'email': 'nonexistent@example.com',
            'code': '123456',
            'password': 'new_password',
            "re_pass": "new_password"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ChangePasswordViewTests(APITestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(email='test@example.com', password='old_password')
        self.url = '/authentication/change-password/'  # Adjust the URL name as per your URL configuration

    def test_change_password_success(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'password': 'old_password',
            'new_password': 'new_password'
        }
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserModel.objects.get(email='test@example.com').check_password('new_password'), True)

    def test_change_password_wrong_password(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'password': 'wrong_password',
            'new_password': 'new_password'
        }
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, 'Wrong password')

    def test_change_password_weak_password(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'password': 'old_password',
            'new_password': 'weak'
        }
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, ['This password is too short. It must contain at least 8 characters.'])

    # def test_change_password_same_password(self):
    #     self.client.force_authenticate(user=self.user)
    #     data = {
    #         'password': 'old_password',
    #         'new_password': 'old_password'
    #     }
    #     response = self.client.put(self.url, data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(response.data, ['The new password must be different from the old password.'])

    def test_change_password_unauthenticated(self):
        data = {
            'password': 'old_password',
            'new_password': 'new_password'
        }
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class VerifyAuthTokenAndGetUserDataViewTests(APITestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(email='test@example.com', password='test_password')
        token, created = Token.objects.get_or_create(user=self.user)
        self.token = str(token)
        self.url = '/authentication/verify-token/'  # Adjust the URL name as per your URL configuration

    def test_verify_auth_token_and_get_user_data_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], self.user.pk)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['is_verified'], self.user.is_verified)
        self.assertEqual(response.data['token'], self.token)

    def test_verify_auth_token_and_get_user_data_unauthenticated(self):
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
