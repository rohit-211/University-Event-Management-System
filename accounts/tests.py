from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.management import call_command
from django.core.exceptions import PermissionDenied
import io

from accounts.models import UserProfile, Role, get_or_create_profile
from accounts.forms import StudentRegistrationForm, UserProfileUpdateForm
from accounts.decorators import role_required, student_required, organiser_required, admin_required

User = get_user_model()


class AccountsModelAndSignalsTests(TestCase):
    """
    Tests for UserProfile model creation, safe signals, and profile backfilling.
    """

    def test_user_creation_signal_creates_student_profile(self):
        """Newly created standard users should automatically receive a STUDENT profile."""
        user = User.objects.create_user(username='student1', password='TestPassword123!', email='student1@uni.edu')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.role, Role.STUDENT)
        self.assertTrue(user.profile.is_student)
        self.assertFalse(user.profile.is_organiser)
        self.assertFalse(user.profile.is_admin_role)

    def test_superuser_creation_signal_creates_admin_profile(self):
        """Newly created superusers should automatically receive an ADMIN profile."""
        admin_user = User.objects.create_superuser(username='super1', password='AdminPass123!', email='admin@uni.edu')
        self.assertTrue(hasattr(admin_user, 'profile'))
        self.assertEqual(admin_user.profile.role, Role.ADMIN)
        self.assertTrue(admin_user.profile.is_admin_role)

    def test_get_or_create_profile_safe_for_existing_users(self):
        """Users without an existing profile should be safely resolved without throwing DoesNotExist."""
        # Create user and deliberately delete the automatically created profile to simulate legacy user
        legacy_user = User.objects.create_user(username='legacy_user', password='LegacyPass123!')
        UserProfile.objects.filter(user=legacy_user).delete()
        legacy_user.refresh_from_db()

        # get_or_create_profile should resolve safely
        profile = get_or_create_profile(legacy_user)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.role, Role.STUDENT)

    def test_setup_profiles_command_backfills_without_overwriting(self):
        """The setup_profiles management command must create missing profiles and preserve existing ones."""
        # 1. Existing user with Organiser role
        org_user = User.objects.create_user(username='existing_org', password='OrgPass123!')
        org_user.profile.role = Role.ORGANISER
        org_user.profile.save()

        # 2. Existing user missing a profile
        missing_user = User.objects.create_user(username='missing_profile_user', password='Pass123!')
        UserProfile.objects.filter(user=missing_user).delete()

        # Run command
        out = io.StringIO()
        call_command('setup_profiles', stdout=out)

        # Verify existing role was NOT overwritten
        org_user.refresh_from_db()
        self.assertEqual(org_user.profile.role, Role.ORGANISER)

        # Verify missing profile was created
        missing_user.refresh_from_db()
        self.assertEqual(missing_user.profile.role, Role.STUDENT)


class RegistrationAndSecurityTests(TestCase):
    """
    Tests for public registration security, password hashing, and role isolation.
    """

    def setUp(self):
        self.client = Client()

    def test_student_registration_success_and_password_hashing(self):
        """Student registration hashes password securely and assigns STUDENT role."""
        payload = {
            'username': 'freshstudent',
            'first_name': 'Fresh',
            'last_name': 'Student',
            'email': 'fresh@uni.edu',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!',
            'department': 'Computer Science',
            'phone_number': '9876543210'
        }
        response = self.client.post(reverse('accounts:register'), data=payload)
        self.assertRedirects(response, reverse('accounts:login'))

        user = User.objects.get(username='freshstudent')
        self.assertTrue(user.check_password('StrongPassword123!'))
        self.assertEqual(user.profile.role, Role.STUDENT)
        self.assertEqual(user.profile.department, 'Computer Science')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_registration_password_mismatch_fails(self):
        """Registration should fail when passwords do not match."""
        payload = {
            'username': 'student_mismatch',
            'first_name': 'Student',
            'last_name': 'Mismatch',
            'email': 'mismatch@uni.edu',
            'password': 'StrongPassword123!',
            'password_confirm': 'DifferentPassword456!',
        }
        response = self.client.post(reverse('accounts:register'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='student_mismatch').exists())

    def test_public_registration_cannot_assign_privileged_roles(self):
        """Tampered POST payloads attempting to inject role=ADMIN must be ignored/rejected."""
        payload = {
            'username': 'hacker_student',
            'first_name': 'Hacker',
            'last_name': 'User',
            'email': 'hacker@uni.edu',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!',
            'role': Role.ADMIN,  # Tampered field injection
            'is_staff': True,
            'is_superuser': True
        }
        self.client.post(reverse('accounts:register'), data=payload)
        user = User.objects.get(username='hacker_student')
        self.assertEqual(user.profile.role, Role.STUDENT)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)


class AuthenticationAndRoutingTests(TestCase):
    """
    Tests for login, logout, and role-based redirect destinations.
    """

    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(username='student_user', password='Password123!')
        self.student.profile.role = Role.STUDENT
        self.student.profile.save()

        self.organiser = User.objects.create_user(username='org_user', password='Password123!')
        self.organiser.profile.role = Role.ORGANISER
        self.organiser.profile.save()

        self.admin = User.objects.create_user(username='admin_user', password='Password123!')
        self.admin.profile.role = Role.ADMIN
        self.admin.profile.save()

    def test_login_and_student_redirect(self):
        """Student login should route to student dashboard."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'student_user',
            'password': 'Password123!'
        })
        self.assertRedirects(response, reverse('accounts:student_dashboard'))

    def test_login_and_organiser_redirect(self):
        """Organiser login should route to organiser dashboard."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'org_user',
            'password': 'Password123!'
        })
        self.assertRedirects(response, reverse('accounts:organiser_dashboard'))

    def test_login_and_admin_redirect(self):
        """Admin login should route to admin dashboard."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'admin_user',
            'password': 'Password123!'
        })
        self.assertRedirects(response, reverse('accounts:admin_dashboard'))

    def test_invalid_login_credentials(self):
        """Invalid credentials should show an error and stay on the login page."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'student_user',
            'password': 'WrongPassword!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_logout_post_redirects_to_home(self):
        """POST logout should invalidate session and redirect to home."""
        self.client.login(username='student_user', password='Password123!')
        response = self.client.post(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('home'))

    def test_logout_get_redirects_safely(self):
        """GET request to logout should redirect safely to home without crashing."""
        self.client.login(username='student_user', password='Password123!')
        response = self.client.get(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('home'))


class DashboardPermissionsAndAccessControlTests(TestCase):
    """
    Tests for role-based access control, server-side permissions, and privilege enforcement.
    """

    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(username='student_jane', password='Password123!')
        self.student.profile.role = Role.STUDENT
        self.student.profile.save()

        self.organiser = User.objects.create_user(username='org_bob', password='Password123!')
        self.organiser.profile.role = Role.ORGANISER
        self.organiser.profile.save()

        self.admin = User.objects.create_user(username='admin_alice', password='Password123!')
        self.admin.profile.role = Role.ADMIN
        self.admin.profile.save()

    def test_unauthenticated_dashboard_access_redirects_to_login(self):
        """Unauthenticated requests to any dashboard must redirect to login with ?next."""
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('accounts:login')))

    def test_student_cannot_access_organiser_dashboard(self):
        """A student accessing organiser dashboard must receive HTTP 403 Forbidden."""
        self.client.login(username='student_jane', password='Password123!')
        response = self.client.get(reverse('accounts:organiser_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_student_cannot_access_admin_dashboard(self):
        """A student accessing admin dashboard must receive HTTP 403 Forbidden."""
        self.client.login(username='student_jane', password='Password123!')
        response = self.client.get(reverse('accounts:admin_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_organiser_cannot_access_admin_dashboard(self):
        """An organiser accessing admin dashboard must receive HTTP 403 Forbidden."""
        self.client.login(username='org_bob', password='Password123!')
        response = self.client.get(reverse('accounts:admin_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_admin_dashboard(self):
        """An admin can successfully access the admin dashboard."""
        self.client.login(username='admin_alice', password='Password123!')
        response = self.client.get(reverse('accounts:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/admin_dashboard.html')

    def test_profile_update_cannot_escalate_role(self):
        """Editing personal profile must update details but strictly prevent role escalation."""
        self.client.login(username='student_jane', password='Password123!')
        payload = {
            'first_name': 'JaneUpdated',
            'last_name': 'DoeUpdated',
            'email': 'jane.updated@uni.edu',
            'department': 'Robotics',
            'phone_number': '1234567890',
            'role': Role.ADMIN  # Malicious escalation attempt
        }
        response = self.client.post(reverse('accounts:profile'), data=payload)
        self.assertRedirects(response, reverse('accounts:profile'))

        self.student.refresh_from_db()
        self.assertEqual(self.student.first_name, 'JaneUpdated')
        self.assertEqual(self.student.profile.department, 'Robotics')
        # Role must still be STUDENT
        self.assertEqual(self.student.profile.role, Role.STUDENT)

    def test_admin_can_change_user_role(self):
        """Administrators can promote a student to organiser."""
        self.client.login(username='admin_alice', password='Password123!')
        response = self.client.post(
            reverse('accounts:change_role', kwargs={'user_id': self.student.pk}),
            data={'role': Role.ORGANISER}
        )
        self.assertRedirects(response, reverse('accounts:admin_dashboard'))
        self.student.refresh_from_db()
        self.assertEqual(self.student.profile.role, Role.ORGANISER)

    def test_non_admin_cannot_change_roles(self):
        """A student or organiser cannot execute the change_role endpoint."""
        self.client.login(username='student_jane', password='Password123!')
        response = self.client.post(
            reverse('accounts:change_role', kwargs={'user_id': self.student.pk}),
            data={'role': Role.ADMIN}
        )
        self.assertEqual(response.status_code, 403)
        self.student.refresh_from_db()
        self.assertEqual(self.student.profile.role, Role.STUDENT)

    def test_existing_application_routes_resolve(self):
        """Verify that core existing application routes continue to resolve properly."""
        self.assertEqual(reverse('home'), '/')
        self.assertEqual(reverse('accounts:login'), '/accounts/login/')
        self.assertEqual(reverse('accounts:register'), '/accounts/register/')
        self.assertEqual(reverse('accounts:logout'), '/accounts/logout/')
        self.assertEqual(reverse('accounts:student_dashboard'), '/accounts/dashboard/student/')
        self.assertEqual(reverse('accounts:organiser_dashboard'), '/accounts/dashboard/organiser/')
        self.assertEqual(reverse('accounts:admin_dashboard'), '/accounts/dashboard/admin/')
