from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import UserProfile, Role


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Signal receiver that ensures every Django User has an associated UserProfile.
    - For new users: creates a UserProfile with Role.ADMIN for superusers/staff,
      or Role.STUDENT for standard registered users.
    - Non-destructive: will never overwrite an existing profile's role or details.
    """
    if created:
        initial_role = Role.ADMIN if (instance.is_superuser or instance.is_staff) else Role.STUDENT
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={'role': initial_role}
        )
