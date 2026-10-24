from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserProfile, Role

User = get_user_model()


class StudentRegistrationForm(forms.ModelForm):
    """
    Public student self-registration form.
    - Excludes role selection entirely: role is strictly assigned as STUDENT on the server.
    - Validates matching passwords and enforces Django's configured password validation rules.
    - Enforces uniqueness for both username and email.
    """
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'First Name', 'class': 'form-input'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Last Name', 'class': 'form-input'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'University Email', 'class': 'form-input'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter strong password', 'class': 'form-input'}),
        help_text="Must contain at least 8 characters and not be too common."
    )
    password_confirm = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your password', 'class': 'form-input'})
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Department (e.g. Computer Science)', 'class': 'form-input'})
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Phone Number (Optional)', 'class': 'form-input'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Student ID / Username', 'class': 'form-input'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm:
            if password != password_confirm:
                self.add_error('password_confirm', "Passwords do not match. Please re-enter.")
            else:
                # Validate against Django's configured password validators
                try:
                    validate_password(password)
                except ValidationError as e:
                    self.add_error('password', e)
        return cleaned_data

    def save(self, commit=True):
        # Save user instance without committing yet to hash the password safely
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        # Public registration never grants staff or superuser privileges
        user.is_staff = False
        user.is_superuser = False

        if commit:
            user.save()
            # Explicitly create or update the profile with Role.STUDENT
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = Role.STUDENT
            profile.department = self.cleaned_data.get('department', '').strip()
            profile.phone_number = self.cleaned_data.get('phone_number', '').strip()
            profile.save()

        return user


class LoginForm(forms.Form):
    """
    Standard authentication form for all application roles.
    """
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your username or student ID',
            'class': 'form-input',
            'autofocus': True
        })
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your password',
            'class': 'form-input'
        })
    )


class UserProfileUpdateForm(forms.ModelForm):
    """
    Profile update form for users editing their personal information.
    Note: The 'role' field is strictly omitted to prevent privilege escalation.
    """
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-input'})
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop('profile', None)
        super().__init__(*args, **kwargs)
        if self.profile:
            self.fields['department'].initial = self.profile.department
            self.fields['phone_number'].initial = self.profile.phone_number

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        # Ensure email is unique across other users
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This email address is already in use by another account.")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        if self.profile and commit:
            self.profile.department = self.cleaned_data.get('department', '').strip()
            self.profile.phone_number = self.cleaned_data.get('phone_number', '').strip()
            # Do NOT update self.profile.role here under any circumstances
            self.profile.save()
        return user


class AdminRoleAssignmentForm(forms.Form):
    """
    Admin-only form for managing and assigning application roles to users.
    """
    role = forms.ChoiceField(
        choices=Role.choices,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
