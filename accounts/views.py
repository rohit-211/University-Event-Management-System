from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse
from django.apps import apps

from .models import UserProfile, Role, get_or_create_profile
from .forms import (
    StudentRegistrationForm,
    LoginForm,
    UserProfileUpdateForm,
    AdminRoleAssignmentForm
)
from .decorators import student_required, organiser_required, admin_required

User = get_user_model()


def get_dashboard_url_for_user(user):
    """
    Helper function to determine the appropriate dashboard URL based on user role.
    """
    profile = get_or_create_profile(user)
    if user.is_superuser or profile.role == Role.ADMIN:
        return reverse('accounts:admin_dashboard')
    elif profile.role == Role.ORGANISER:
        return reverse('accounts:organiser_dashboard')
    return reverse('accounts:student_dashboard')


def register_view(request):
    """
    Student public self-registration view.
    Always assigns the STUDENT role; never accepts privileged roles from input.
    """
    if request.user.is_authenticated:
        return redirect(get_dashboard_url_for_user(request.user))

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Registration successful! Welcome to UEMS, {user.first_name}. Please log in."
            )
            return redirect('accounts:login')
        else:
            messages.error(request, "Please correct the registration errors below.")
    else:
        form = StudentRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    User login view for all roles.
    Validates credentials, securely establishes session, and redirects to role dashboard.
    """
    if request.user.is_authenticated:
        return redirect(get_dashboard_url_for_user(request.user))

    redirect_to = request.POST.get('next') or request.GET.get('next', '')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username'].strip()
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if not user.is_active:
                    messages.error(request, "This account is inactive. Please contact the administrator.")
                    return render(request, 'accounts/login.html', {'form': form})

                login(request, user)
                # Ensure profile exists safely
                get_or_create_profile(user)

                messages.success(
                    request,
                    f"Welcome back, {user.first_name or user.username}!"
                )

                # Validate safe redirect target, or fallback to role-specific dashboard
                if redirect_to and url_has_allowed_host_and_scheme(
                    url=redirect_to,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure()
                ):
                    return redirect(redirect_to)

                return redirect(get_dashboard_url_for_user(user))
            else:
                messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': redirect_to})


def logout_view(request):
    """
    User logout view.
    Requires POST method to prevent CSRF logout vulnerabilities.
    """
    if request.method == 'POST':
        logout(request)
        messages.info(request, "You have been successfully logged out.")
        return redirect('home')

    # If accessed via GET, redirect to home safely
    return redirect('home')


@login_required
def dashboard_redirect_view(request):
    """
    Dynamic hub that routes authenticated users to their corresponding dashboard.
    """
    return redirect(get_dashboard_url_for_user(request.user))


@student_required
def student_dashboard_view(request):
    """
    Dashboard tailored for Students:
    Displays registered events, upcoming published events, attendance records, and announcements.
    """
    profile = get_or_create_profile(request.user)

    # Safely query existing models from other apps if implemented
    registered_events = []
    upcoming_events = []
    attendance_records = []
    announcements = []

    # Safely check if Event model exists in events app
    if apps.is_installed('events'):
        try:
            Event = apps.get_model('events', 'Event')
            upcoming_events = Event.objects.filter(is_published=True)[:5]
        except (LookupError, Exception):
            pass

    # Safely check if Registration model exists in registrations app
    if apps.is_installed('registrations'):
        try:
            Registration = apps.get_model('registrations', 'Registration')
            registered_events = Registration.objects.filter(user=request.user).select_related('event')
        except (LookupError, Exception):
            pass

    # Safely check if Attendance model exists in attendance app
    if apps.is_installed('attendance'):
        try:
            Attendance = apps.get_model('attendance', 'Attendance')
            attendance_records = Attendance.objects.filter(user=request.user)
        except (LookupError, Exception):
            pass

    # Safely check if Announcement model exists in announcements app
    if apps.is_installed('announcements'):
        try:
            Announcement = apps.get_model('announcements', 'Announcement')
            announcements = Announcement.objects.all().order_by('-created_at')[:5]
        except (LookupError, Exception):
            pass

    context = {
        'profile': profile,
        'registered_events': registered_events,
        'upcoming_events': upcoming_events,
        'attendance_records': attendance_records,
        'announcements': announcements,
    }
    return render(request, 'accounts/student_dashboard.html', context)


@organiser_required
def organiser_dashboard_view(request):
    """
    Dashboard tailored for Organisers:
    Displays organiser's created events, attendee statistics, registration links, and attendance controls.
    """
    profile = get_or_create_profile(request.user)

    my_events = []
    total_registrations = 0
    announcements = []

    # Safely check if Event model exists and check for organiser field
    if apps.is_installed('events'):
        try:
            Event = apps.get_model('events', 'Event')
            # Check if 'organiser' or 'creator' field exists
            field_names = [f.name for f in Event._meta.get_fields()]
            if 'organiser' in field_names:
                my_events = Event.objects.filter(organiser=request.user)
            elif 'creator' in field_names:
                my_events = Event.objects.filter(creator=request.user)
            elif 'created_by' in field_names:
                my_events = Event.objects.filter(created_by=request.user)
            elif 'user' in field_names:
                my_events = Event.objects.filter(user=request.user)
            else:
                my_events = Event.objects.all()[:10]
        except (LookupError, Exception):
            pass

    if apps.is_installed('announcements'):
        try:
            Announcement = apps.get_model('announcements', 'Announcement')
            announcements = Announcement.objects.all().order_by('-created_at')[:5]
        except (LookupError, Exception):
            pass

    context = {
        'profile': profile,
        'my_events': my_events,
        'total_registrations': total_registrations,
        'announcements': announcements,
    }
    return render(request, 'accounts/organiser_dashboard.html', context)


@admin_required
def admin_dashboard_view(request):
    """
    Dashboard tailored for Administrators:
    Provides platform-wide metrics, user role management, system oversight, and fast navigation.
    """
    profile = get_or_create_profile(request.user)

    # Real database statistics
    total_users = User.objects.count()
    student_count = UserProfile.objects.filter(role=Role.STUDENT).count()
    organiser_count = UserProfile.objects.filter(role=Role.ORGANISER).count()
    admin_count = UserProfile.objects.filter(role=Role.ADMIN).count()

    # User accounts with their profiles
    all_users = User.objects.select_related('profile').all().order_by('-date_joined')

    # Event count if model exists
    total_events = 0
    if apps.is_installed('events'):
        try:
            Event = apps.get_model('events', 'Event')
            total_events = Event.objects.count()
        except (LookupError, Exception):
            pass

    # Registration count if model exists
    total_registrations = 0
    if apps.is_installed('registrations'):
        try:
            Registration = apps.get_model('registrations', 'Registration')
            total_registrations = Registration.objects.count()
        except (LookupError, Exception):
            pass

    context = {
        'profile': profile,
        'total_users': total_users,
        'student_count': student_count,
        'organiser_count': organiser_count,
        'admin_count': admin_count,
        'total_events': total_events,
        'total_registrations': total_registrations,
        'all_users': all_users,
        'role_choices': Role.choices,
    }
    return render(request, 'accounts/admin_dashboard.html', context)


@admin_required
def change_role_view(request, user_id):
    """
    Admin-only endpoint to assign or modify a user's application role.
    Strictly prevents privilege escalation and accidental self-lockout.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('accounts:admin_dashboard')

    target_user = get_object_or_404(User, pk=user_id)
    target_profile = get_or_create_profile(target_user)

    form = AdminRoleAssignmentForm(request.POST)
    if form.is_valid():
        new_role = form.cleaned_data['role']

        # Prevent admin from demoting themselves if they are currently the only active admin
        if target_user == request.user and new_role != Role.ADMIN:
            admin_count = UserProfile.objects.filter(role=Role.ADMIN).count()
            if admin_count <= 1:
                messages.error(
                    request,
                    "Security restriction: You cannot demote yourself because you are the sole administrator."
                )
                return redirect('accounts:admin_dashboard')

        target_profile.role = new_role
        target_profile.save()
        messages.success(
            request,
            f"Role for user '{target_user.username}' successfully changed to {target_profile.get_role_display()}."
        )
    else:
        messages.error(request, "Invalid role selection.")

    return redirect('accounts:admin_dashboard')


@login_required
def profile_view(request):
    """
    User profile view allowing viewing and updating personal details.
    Restricted to safe personal fields (first_name, last_name, email, department, phone_number).
    Application role is strictly read-only for standard users.
    """
    profile = get_or_create_profile(request.user)

    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=request.user, profile=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile details have been updated successfully.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors in the profile form.")
    else:
        form = UserProfileUpdateForm(instance=request.user, profile=profile)

    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile': profile,
    })
