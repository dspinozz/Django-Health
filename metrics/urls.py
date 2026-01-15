"""
URL routing for the Health Metrics API.

Uses DRF's DefaultRouter for automatic URL generation from ViewSets.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'metric-types', views.MetricTypeViewSet, basename='metrictype')
router.register(r'metrics', views.HealthMetricViewSet, basename='healthmetric')
router.register(r'goals', views.GoalViewSet, basename='goal')
router.register(r'profile', views.UserProfileViewSet, basename='profile')
router.register(r'auth', views.AuthViewSet, basename='auth')
router.register(r'dashboard', views.DashboardViewSet, basename='dashboard')

urlpatterns = [
    # API routes from router
    path('', include(router.urls)),
    
    # Token authentication endpoint
    path('auth/token/', obtain_auth_token, name='api-token'),
]
