"""
Health Metrics Models

Demonstrates Django ORM patterns:
- Model relationships (ForeignKey, choices)
- Field validation and constraints
- Custom model methods
- Meta options and ordering
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import date


class MetricType(models.Model):
    """
    Defines types of health metrics that can be tracked.
    Examples: steps, sleep_hours, water_intake, weight, heart_rate
    """
    name = models.CharField(max_length=50, unique=True)
    unit = models.CharField(max_length=20, help_text="Unit of measurement (e.g., steps, hours, ml, kg)")
    description = models.TextField(blank=True)
    min_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Minimum valid value for this metric"
    )
    max_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Maximum valid value for this metric"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Metric Type'
        verbose_name_plural = 'Metric Types'

    def __str__(self):
        return f"{self.name} ({self.unit})"


class HealthMetric(models.Model):
    """
    Individual health metric entries recorded by users.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='health_metrics'
    )
    metric_type = models.ForeignKey(
        MetricType, 
        on_delete=models.PROTECT, 
        related_name='entries'
    )
    value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    recorded_date = models.DateField(default=date.today)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-recorded_date', '-created_at']
        verbose_name = 'Health Metric'
        verbose_name_plural = 'Health Metrics'
        # Ensure one entry per metric type per day per user
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'metric_type', 'recorded_date'],
                name='unique_daily_metric'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'recorded_date']),
            models.Index(fields=['metric_type', 'recorded_date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.metric_type.name}: {self.value} ({self.recorded_date})"

    def clean(self):
        """Validate value is within metric type bounds."""
        from django.core.exceptions import ValidationError
        if self.metric_type:
            if self.metric_type.min_value and self.value < self.metric_type.min_value:
                raise ValidationError(
                    f"Value must be at least {self.metric_type.min_value} for {self.metric_type.name}"
                )
            if self.metric_type.max_value and self.value > self.metric_type.max_value:
                raise ValidationError(
                    f"Value must be at most {self.metric_type.max_value} for {self.metric_type.name}"
                )


class Goal(models.Model):
    """
    Health goals set by users for specific metric types.
    """
    class GoalType(models.TextChoices):
        DAILY = 'DAILY', 'Daily'
        WEEKLY = 'WEEKLY', 'Weekly'
        MONTHLY = 'MONTHLY', 'Monthly'

    class GoalDirection(models.TextChoices):
        INCREASE = 'INCREASE', 'Increase (reach or exceed target)'
        DECREASE = 'DECREASE', 'Decrease (stay at or below target)'
        MAINTAIN = 'MAINTAIN', 'Maintain (stay within range)'

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='goals'
    )
    metric_type = models.ForeignKey(
        MetricType, 
        on_delete=models.PROTECT, 
        related_name='goals'
    )
    target_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    goal_type = models.CharField(
        max_length=10, 
        choices=GoalType.choices, 
        default=GoalType.DAILY
    )
    direction = models.CharField(
        max_length=10,
        choices=GoalDirection.choices,
        default=GoalDirection.INCREASE
    )
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Goal'
        verbose_name_plural = 'Goals'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'metric_type', 'goal_type'],
                condition=models.Q(is_active=True),
                name='unique_active_goal_per_type'
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.metric_type.name} {self.goal_type}: {self.target_value}"

    @property
    def is_expired(self):
        """Check if the goal has passed its end date."""
        if self.end_date:
            return timezone.now().date() > self.end_date
        return False


class UserProfile(models.Model):
    """
    Extended user profile for health-related settings.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    date_of_birth = models.DateField(null=True, blank=True)
    height_cm = models.PositiveIntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(300)]
    )
    timezone = models.CharField(max_length=50, default='UTC')
    notifications_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"Profile: {self.user.username}"

    @property
    def age(self):
        """Calculate user's age from date of birth."""
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
