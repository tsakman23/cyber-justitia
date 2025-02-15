"""
Test cases for user views.

Author: Ionut-Valeriu Facaeru, Georgios Tsakoumakis
"""

import unittest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from ..models import ProfessionalUser

CustomUser = get_user_model()


class AuthViewsTestCase(TestCase):
    """
    Test case for authentication views.
    """

    def setUp(self):
        """
        TUV1: Set up a test client and user for use in the tests.
        """
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            first_name='Test',
            last_name='User',
            email='testuser@example.com',
            password='Password123!'
        )

    def test_render_index_page(self):
        """
        TUV2: Test that the index page renders correctly.
        """
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_unauthenticated_user_accesses_register_page(self):
        """
        TUV3: Test that an unauthenticated user can access the register page.
        """
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    def test_authenticated_user_accesses_register_page(self):
        """
        TUV4: Test that an authenticated user is redirected from the register page.
        """
        self.client.force_login(self.user)
        response = self.client.get(reverse('register'))
        self.assertRedirects(response, '/chatbot/', target_status_code=302)

    def test_register_new_standard_user_with_valid_data(self):
        """
        TUV5: Test that a new standard user can register with valid data.
        """
        response = self.client.post(reverse('register'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'johndoe',
            'email': 'johndoe@example.com',
            'password': 'Password123!',
            'password2': 'Password123!',
            'user_type': 'standard'
        })
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(CustomUser.objects.filter(username='johndoe').exists())

    def test_register_new_professional_user_with_valid_data(self):
        """
        TUV6: Test that a new professional user can register with valid data.
        """
        response = self.client.post(reverse('register'), {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'username': 'janedoe',
            'email': 'janedoe@example.com',
            'password': 'Password123!',
            'password2': 'Password123!',
            'user_type': 'professional',
            'flair': 'Experienced Attorney'
        })
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(CustomUser.objects.filter(username='janedoe').exists())
        self.assertTrue(ProfessionalUser.objects.filter(user__username='janedoe').exists())

    def test_register_user_with_weak_password(self):
        """
        TUV7: Test that a weak password prevents registration.
        """
        response = self.client.post(reverse('register'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'johndoe',
            'email': 'johndoe@example.com',
            'password': 'weak',
            'password2': 'weak',
            'user_type': 'standard'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password not strong enough')

    def test_register_user_with_non_matching_passwords(self):
        """
        TUV8: Test that non-matching passwords prevent registration.
        """
        response = self.client.post(reverse('register'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'johndoe',
            'email': 'johndoe@example.com',
            'password': 'Strongpassword123!',
            'password2': 'differentpassword',
            'user_type': 'standard'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password not matching')

    def test_register_user_with_existing_username(self):
        """
        TUV9: Test that an existing username prevents registration.
        """
        response = self.client.post(reverse('register'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'testuser',  # existing username
            'email': 'johndoe@example.com',
            'password': 'Password123!',
            'password2': 'Password123!',
            'user_type': 'standard'
        }, follow=True)
        self.assertRedirects(response, reverse('register'))
        self.assertContains(response, 'Username already exists')

    def test_register_user_with_existing_email(self):
        """
        TUV10: Test that an existing email prevents registration.
        """
        response = self.client.post(reverse('register'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'johndoe',
            'email': 'testuser@example.com',  # existing email
            'password': 'Password123!',
            'password2': 'Password123!',
            'user_type': 'standard'
        }, follow=True)
        self.assertRedirects(response, reverse('register'))
        self.assertContains(response, 'Email already exists')

    def test_unauthenticated_user_accesses_login_page(self):
        """
        TUV11: Test that an unauthenticated user can access the login page.
        """
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_authenticated_user_accesses_login_page(self):
        """
        TUV12: Test that an authenticated user is redirected from the login page.
        """
        self.client.force_login(self.user)
        response = self.client.get(reverse('login'))
        self.assertRedirects(response, '/chatbot/', target_status_code=302)

    def test_login_with_valid_credentials(self):
        """
        TUV13: Test that a user can log in with valid credentials.
        """
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'Password123!'
        })
        self.assertRedirects(response, '/chatbot/', target_status_code=302)

    def test_login_with_invalid_credentials(self):
        """
        TUV14: Test that logging in with invalid credentials fails.
        """
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        }, follow=True)
        self.assertRedirects(response, reverse('login'))
        self.assertContains(response, 'Invalid credentials')

    def test_authenticated_user_logs_out(self):
        """
        TUV15: Test that an authenticated user can log out.
        """
        self.client.force_login(self.user)
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, '/')
        self.assertNotIn('_auth_user_id', self.client.session)


class DashboardViewsTestCase(TestCase):
    """
    Test case for dashboard views.
    """

    def setUp(self):
        """
        TUV16: Set up a test client and user for use in the tests.
        """
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            first_name='Test',
            last_name='User',
            email='testuser@example.com',
            password='Password123!'
        )
        self.client.force_login(self.user)

    def test_dashboard_page_access(self):
        """
        TUV17: Test that the dashboard page is accessible.
        """
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')

    def test_update_details_with_valid_data(self):
        """
        TUV18: Test updating user details with valid data.
        """
        new_first_name = 'UpdatedFirstName'
        new_last_name = 'UpdatedLastName'
        new_email = 'updatedemail@example.com'

        response = self.client.post(reverse('dashboard'), {
            'first_name': new_first_name,
            'last_name': new_last_name,
            'email': new_email,
            'update_details': '1'
        })

        # Check that the user is redirected to the dashboard after a successful update
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

        # Fetch the updated user details from the database
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, new_first_name)
        self.assertEqual(self.user.last_name, new_last_name)
        self.assertEqual(self.user.email, new_email)

    def test_update_first_name_with_blank_value(self):
        """
        TUV19: Test that updating first name with a blank value fails.
        """
        response = self.client.post(reverse('update_details'), {
            'first_name': '',
            'last_name': 'User',
            'email': 'testuser@example.com'
        })

        # Check that the form is re-rendered with errors
        self.assertEqual(response.status_code, 200)
        form = response.context['update_details_form']
        self.assertTrue(form.errors)
        self.assertIn('first_name', form.errors)
        self.assertEqual(form.errors['first_name'], ['First name field is required.'])

    def test_update_last_name_with_blank_value(self):
        """
        TUV20: Test that updating last name with a blank value fails.
        """
        response = self.client.post(reverse('update_details'), {
            'first_name': 'Test',
            'last_name': '',  # Attempting to update last name with a blank value
            'email': 'testuser@example.com'
        })

        # Check that the form is re-rendered with errors
        self.assertEqual(response.status_code, 200)
        form = response.context['update_details_form']
        self.assertTrue(form.errors)
        self.assertIn('last_name', form.errors)
        self.assertEqual(form.errors['last_name'], ['Last name field is required.'])

    def test_update_password_with_valid_field(self):
        """
        TUV21: Test updating the password with valid data.
        """
        response = self.client.post(reverse('dashboard'), {
            'old_password': 'Password123!',
            'new_password1': 'NewPassword123!',
            'new_password2': 'NewPassword123!'
        })

        # Check that the password is updated successfully and the user is redirected
        self.assertEqual(response.status_code, 200)  # Redirect status code

        # Check that the new password works for login
        self.client.logout()
        login_response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'NewPassword123!'
        })
        self.assertEqual(login_response.status_code, 302)

    def test_change_password_mismatch(self):
        """
        TUV22: Test that changing the password with mismatched new passwords fails.
        """
        response = self.client.post(reverse('dashboard'), {
            'old_password': 'Password123!',
            'new_password1': 'NewPassword123!',
            'new_password2': 'DifferentPassword123!',  # New passwords do not match
            'change_password': '1'  # Identify which form is being submitted
        })

        # Check that the form is re-rendered with errors
        self.assertEqual(response.status_code, 200)
        form = response.context['change_password_form']
        self.assertTrue(form.errors)
        self.assertIn('new_password2', form.errors)
        self.assertEqual(form.errors['new_password2'], ['The new passwords do not match.'])

    def test_change_password_with_blank_field(self):
        """
        TUV23: Test that changing the password with blank fields fails.
        """
        response = self.client.post(reverse('dashboard'), {
            'old_password': '',
            'new_password1': '',
            'new_password2': '',
            'change_password': '1'
        })

        # Check that the form is re-rendered with errors
        self.assertEqual(response.status_code, 200)
        form = response.context['change_password_form']
        self.assertEqual(len(form.errors), 3)

    def test_deactivate_account_with_checkbox_checked(self):
        """
        TUV24: Test deactivating the account when the checkbox is checked.
        """
        response = self.client.post(reverse('deactivate_account'), {
                                    'deactivate_profile': '1',
        })
        self.assertRedirects(response, reverse('index'))
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_deactivate_account_without_checkbox_checked(self):
        """
        TUV25: Test that deactivating the account without checking the checkbox fails.
        """
        self.client.force_login(self.user)
        response = self.client.post(reverse('dashboard'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_update_description_with_valid_data(self):
        """
        TUV26: Test updating the user description with valid data.
        """
        response = self.client.post(reverse('update_description'), {
            'description': 'Updated description'
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.description, 'Updated description')

    def test_update_flair_with_valid_data(self):
        """
        TUV27: Test updating the user flair with valid data.
        """
        response = self.client.post(reverse('update_flair'), {
            'flair': 'Updated flair'
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.user.professionaluser.refresh_from_db()
        self.assertEqual(self.user.professionaluser.flair, 'Updated flair')

    def test_update_flair_with_blank_value(self):
        """
        TUV28: Test that updating the flair with a blank value fails.
        """
        response = self.client.post(reverse('update_flair'), {
            'flair': '',  # Attempting to update flair with a blank value
        })

        # Check that the form is re-rendered with errors
        self.assertEqual(response.status_code, 200)
        form = response.context['update_flair_form']
        self.assertTrue(form.errors)
        self.assertIn('flair', form.errors)
        self.assertEqual(form.errors['flair'], ['Flair field is required.'])


if __name__ == '__main__':
    unittest.main()