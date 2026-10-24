from django.db import models
from django.conf import settings


class Role(models.TextChoices):
    """
    Application-level role choices for the University Event Management System.
    - STUDENT: Can browse events, register, view their registrations & attendance.
    - ORGANISER: Can create & manage their own events, view registrations, mark attendance.
    - ADMIN: Can manage user roles, system settings, and oversee all university events.
    """
    STUDENT = 'STUDENT', 'Student'
    ORGANISER = 'ORGANISER', 'Organiser'
    ADMIN = 'ADMIN', 'Admin'


class UserProfile(models.Model):
    """
    Extension profile for Django's built-in User model.
    Maintains a 1-to-1 relationship with settings.AUTH_USER_MODEL.
    Preserves all standard Django auth fields (username, email, password, permissions)
    while adding application-specific role and profile information.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        help_text="The core Django authentication user account."
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        db_index=True,
        help_text="The application-level authorization role."
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        help_text="Optional contact phone number."
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text="Academic department (e.g. Computer Science, Mechanical Engineering)."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the profile was initialized."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the profile was last modified."
    )

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_student(self):
        return self.role == Role.STUDENT

    @property
    def is_organiser(self):
        return self.role == Role.ORGANISER

    @property
    def is_admin_role(self):
        return self.role == Role.ADMIN


def get_or_create_profile(user):
    """
    Safely retrieves or creates a UserProfile for an existing User.
    Ensures that existing users without profiles do not crash the application.
    If the user is a Django superuser, default their application role to ADMIN.
    """
    if hasattr(user, 'profile'):
        return user.profile

    # Determine safe default role: superusers get ADMIN, normal users get STUDENT
    initial_role = Role.ADMIN if (user.is_superuser or user.is_staff) else Role.STUDENT
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={'role': initial_role}
    )
    return profile
