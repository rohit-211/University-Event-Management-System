from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


class UserProfileInline(admin.StackedInline):
    """
    Allows editing the application UserProfile directly inside Django's User admin panel.
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Application Profile & Role'
    fk_name = 'user'
    fields = ('role', 'department', 'phone_number')


class CustomUserAdmin(BaseUserAdmin):
    """
    Extended User admin showing profile role in the main user list.
    """
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff', 'is_active')
    list_select_related = ('profile',)

    @admin.display(description='App Role')
    def get_role(self, instance):
        if hasattr(instance, 'profile'):
            return instance.profile.get_role_display()
        return '-'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Dedicated admin interface for managing UserProfile records.
    """
    list_display = ('user', 'role', 'department', 'phone_number', 'created_at', 'updated_at')
    list_filter = ('role', 'department', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'department', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25


# Re-register User admin with the inline profile
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, CustomUserAdmin)
