from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import UserProfile, Role

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Non-destructive backfill command to ensure all existing users have a UserProfile. "
        "Superusers and staff members without a profile receive the ADMIN role. "
        "All other users without a profile receive the safe default STUDENT role. "
        "Existing profiles and roles are never overwritten."
    )

    def handle(self, *args, **options):
        total_users = User.objects.count()
        created_count = 0
        existing_count = 0

        self.stdout.write(self.style.NOTICE(f"Scanning {total_users} user account(s) for missing profiles..."))

        for user in User.objects.all():
            try:
                profile = user.profile
                existing_count += 1
                self.stdout.write(
                    f" - [KEPT] User '{user.username}' (ID: {user.pk}) already has profile with role: {profile.role}"
                )
            except UserProfile.DoesNotExist:
                # Assign ADMIN to superusers or staff, STUDENT to standard users
                assigned_role = Role.ADMIN if (user.is_superuser or user.is_staff) else Role.STUDENT
                profile = UserProfile.objects.create(user=user, role=assigned_role)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f" + [CREATED] Profile for user '{user.username}' (ID: {user.pk}) assigned role: {assigned_role}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSummary: {created_count} profile(s) created, {existing_count} existing profile(s) preserved intact."
            )
        )
