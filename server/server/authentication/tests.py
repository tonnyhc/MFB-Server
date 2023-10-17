from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

class AppUserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpassword'
        }
        self.user = get_user_model().objects.create_user(**self.user_data)

    def test_create_user(self):
        self.assertTrue(isinstance(self.user, get_user_model()))
        self.assertEqual(self.user.email, self.user_data['email'])
        self.assertEqual(self.user.username, self.user_data['username'])
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)

    def test_create_superuser(self):
        admin_user = get_user_model().objects.create_superuser(
            email='admin@example.com',
            password='adminpassword'
        )
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)

    def test_create_user_missing_email(self):
        # Test if creating a user without an email raises a ValueError
        new_user_data = {
            'email': "",
            'username': 'testuser2',
            'password': 'testpassword',
        }

        try:
            get_user_model().objects.create_user(**new_user_data)
        except (ValueError, TypeError) as e:
            self.assertEqual(str(e), 'The Email field must be set')
        else:
            self.fail("Expected ValueError but no exception was raised")
    def test_create_user_with_existing_email(self):
        # Test if creating a user with an existing email raises ValidationError
        with self.assertRaises(ValidationError):
            get_user_model().objects.create_user(**self.user_data)
