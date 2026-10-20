"""
URL Configuration for config (University Event Management System).

The `urlpatterns` list routes URLs to views.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Built-in Django Admin Interface
    path('admin/', admin.site.urls),

    # Project Foundation Landing Page
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # Modular App URL Routes
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('events/', include('events.urls', namespace='events')),
    path('registrations/', include('registrations.urls', namespace='registrations')),
    path('attendance/', include('attendance.urls', namespace='attendance')),
    path('announcements/', include('announcements.urls', namespace='announcements')),
]

# Serve uploaded media files during local development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
