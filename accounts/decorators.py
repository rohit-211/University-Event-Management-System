from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse
from .models import Role, get_or_create_profile


def role_required(*allowed_roles):
    """
    Decorator for views that checks whether a user is authenticated and possesses
    one of the allowed application roles.
    
    Behavior:
    1. If the user is unauthenticated: redirects to the login URL with the 'next' parameter.
    2. If the user is authenticated: safely resolves their UserProfile.
    3. If the user is a superuser or holds an allowed role: proceeds with the view.
    4. If the user holds an unauthorized role: raises PermissionDenied (returns HTTP 403).
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                login_url = settings.LOGIN_URL
                if not login_url.startswith('/'):
                    try:
                        login_url = reverse(login_url)
                    except Exception:
                        login_url = '/accounts/login/'
                return redirect(f"{login_url}?next={request.path}")

            profile = get_or_create_profile(request.user)

            # Django superusers always have full administrative access
            if request.user.is_superuser or profile.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            # Server-side authorization failure: return 403 Forbidden
            raise PermissionDenied("You do not have permission to access this portal page.")
        return _wrapped_view
    return decorator


def student_required(view_func):
    """Decorator ensuring the current user is a STUDENT or superuser."""
    return role_required(Role.STUDENT)(view_func)


def organiser_required(view_func):
    """Decorator ensuring the current user is an ORGANISER or superuser."""
    return role_required(Role.ORGANISER)(view_func)


def admin_required(view_func):
    """Decorator ensuring the current user has the ADMIN application role or superuser."""
    return role_required(Role.ADMIN)(view_func)
