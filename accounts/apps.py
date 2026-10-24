from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'User Accounts & Roles'

    def ready(self):
        # Import signal handlers to ensure profiles are created safely on user creation
        import accounts.signals  # noqa
