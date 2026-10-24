from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication routes
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Profile routes
    path('profile/', views.profile_view, name='profile'),

    # Role-based dashboard routes
    path('dashboard/', views.dashboard_redirect_view, name='dashboard'),
    path('dashboard/student/', views.student_dashboard_view, name='student_dashboard'),
    path('dashboard/organiser/', views.organiser_dashboard_view, name='organiser_dashboard'),
    path('dashboard/admin/', views.admin_dashboard_view, name='admin_dashboard'),

    # Admin role management route
    path('admin/change-role/<int:user_id>/', views.change_role_view, name='change_role'),
]
