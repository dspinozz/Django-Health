"""
Django Admin configuration for Health Metrics models.
"""

from django.contrib import admin
from .models import MetricType, HealthMetric, Goal, UserProfile


@admin.register(MetricType)
class MetricTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'unit', 'min_value', 'max_value', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(HealthMetric)
class HealthMetricAdmin(admin.ModelAdmin):
    list_display = ['user', 'metric_type', 'value', 'recorded_date', 'created_at']
    list_filter = ['metric_type', 'recorded_date', 'created_at']
    search_fields = ['user__username', 'notes']
    ordering = ['-recorded_date', '-created_at']
    date_hierarchy = 'recorded_date'
    raw_id_fields = ['user']


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'metric_type', 'goal_type', 'target_value', 'direction', 'is_active', 'start_date']
    list_filter = ['goal_type', 'direction', 'is_active', 'created_at']
    search_fields = ['user__username']
    ordering = ['-created_at']
    raw_id_fields = ['user']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'date_of_birth', 'height_cm', 'timezone', 'notifications_enabled']
    list_filter = ['notifications_enabled', 'timezone']
    search_fields = ['user__username', 'user__email']
    raw_id_fields = ['user']
