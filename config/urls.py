"""
Main URL configuration for Health Metrics API project.
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def api_root(request):
    """Root endpoint with API information."""
    return JsonResponse({
        'name': 'Health Metrics API',
        'version': '1.0.0',
        'endpoints': {
            'api': '/api/v1/',
            'admin': '/admin/',
            'docs': '/api/v1/docs/',
        }
    })

urlpatterns = [
    # Root endpoint
    path('', api_root, name='api-root'),
    
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API v1 endpoints
    path('api/v1/', include('metrics.urls')),
    
    # DRF browsable API authentication
    path('api-auth/', include('rest_framework.urls')),
]
