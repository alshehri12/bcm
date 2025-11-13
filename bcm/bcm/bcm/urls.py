"""
URL configuration for bcm project.
BCM Management System - Business Continuity Management
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Authentication
    path('accounts/', include('accounts.urls')),

    # Dashboard (Home)
    path('', RedirectView.as_view(pattern_name='dashboard:home', permanent=False)),
    path('dashboard/', include('dashboard.urls')),

    # Risks
    path('risks/', include('risks.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
