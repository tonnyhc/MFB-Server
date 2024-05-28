from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest import mock, TestCase

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
