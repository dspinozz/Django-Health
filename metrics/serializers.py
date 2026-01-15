"""
Django REST Framework Serializers

Demonstrates DRF serializer patterns:
- ModelSerializer with field customization
- Nested serializers
- Custom validation
- Read-only and write-only fields
- SerializerMethodField for computed properties
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db.models import Avg, Sum, Count
from django.utils import timezone
from datetime import timedelta

from .models import MetricType, HealthMetric, Goal, UserProfile


class MetricTypeSerializer(serializers.ModelSerializer):
    """Serializer for MetricType model."""
    
    class Meta:
        model = MetricType
        fields = [
            'id', 'name', 'unit', 'description', 
            'min_value', 'max_value', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MetricTypeListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing metric types."""
    
    class Meta:
        model = MetricType
        fields = ['id', 'name', 'unit']


class HealthMetricSerializer(serializers.ModelSerializer):
    """
    Serializer for HealthMetric model.
    Demonstrates nested serializers and custom validation.
    """
    metric_type = MetricTypeListSerializer(read_only=True)
    metric_type_id = serializers.PrimaryKeyRelatedField(
        queryset=MetricType.objects.filter(is_active=True),
        source='metric_type',
        write_only=True
    )
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = HealthMetric
        fields = [
            'id', 'username', 'metric_type', 'metric_type_id',
            'value', 'recorded_date', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'username', 'created_at', 'updated_at']

    def validate_value(self, value):
        """Ensure value is positive."""
        if value < 0:
            raise serializers.ValidationError("Value must be positive.")
        return value

    def validate(self, attrs):
        """
        Custom validation to ensure value is within metric type bounds.
        """
        metric_type = attrs.get('metric_type')
        value = attrs.get('value')
        
        if metric_type and value is not None:
            if metric_type.min_value and value < metric_type.min_value:
                raise serializers.ValidationError({
                    'value': f"Value must be at least {metric_type.min_value} for {metric_type.name}"
                })
            if metric_type.max_value and value > metric_type.max_value:
                raise serializers.ValidationError({
                    'value': f"Value must be at most {metric_type.max_value} for {metric_type.name}"
                })
        
        return attrs

    def create(self, validated_data):
        """Set the user from the request context."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class HealthMetricCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating health metrics.
    """
    class Meta:
        model = HealthMetric
        fields = ['metric_type', 'value', 'recorded_date', 'notes']

    def validate(self, attrs):
        """Validate metric bounds and check for duplicates."""
        metric_type = attrs.get('metric_type')
        value = attrs.get('value')
        recorded_date = attrs.get('recorded_date', timezone.now().date())
        user = self.context['request'].user

        # Check bounds
        if metric_type and value is not None:
            if metric_type.min_value and value < metric_type.min_value:
                raise serializers.ValidationError({
                    'value': f"Value must be at least {metric_type.min_value}"
                })
            if metric_type.max_value and value > metric_type.max_value:
                raise serializers.ValidationError({
                    'value': f"Value must be at most {metric_type.max_value}"
                })

        # Check for existing entry (for create only)
        if not self.instance:
            existing = HealthMetric.objects.filter(
                user=user,
                metric_type=metric_type,
                recorded_date=recorded_date
            ).exists()
            if existing:
                raise serializers.ValidationError({
                    'recorded_date': f"You already have a {metric_type.name} entry for this date."
                })

        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class GoalSerializer(serializers.ModelSerializer):
    """
    Serializer for Goal model.
    Demonstrates computed properties via SerializerMethodField.
    """
    metric_type = MetricTypeListSerializer(read_only=True)
    metric_type_id = serializers.PrimaryKeyRelatedField(
        queryset=MetricType.objects.filter(is_active=True),
        source='metric_type',
        write_only=True
    )
    is_expired = serializers.BooleanField(read_only=True)
    progress = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Goal
        fields = [
            'id', 'username', 'metric_type', 'metric_type_id',
            'target_value', 'goal_type', 'direction',
            'is_active', 'is_expired', 'progress',
            'start_date', 'end_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'username', 'is_expired', 'progress', 'created_at', 'updated_at']

    def get_progress(self, obj):
        """
        Calculate current progress toward the goal.
        Returns percentage and current value.
        """
        today = timezone.now().date()
        
        # Determine date range based on goal type
        if obj.goal_type == Goal.GoalType.DAILY:
            start = today
            end = today
        elif obj.goal_type == Goal.GoalType.WEEKLY:
            start = today - timedelta(days=today.weekday())
            end = today
        else:  # MONTHLY
            start = today.replace(day=1)
            end = today

        # Get metrics in range
        metrics = HealthMetric.objects.filter(
            user=obj.user,
            metric_type=obj.metric_type,
            recorded_date__gte=start,
            recorded_date__lte=end
        )

        if obj.goal_type == Goal.GoalType.DAILY:
            current_value = metrics.aggregate(Sum('value'))['value__sum'] or 0
        else:
            current_value = metrics.aggregate(Avg('value'))['value__avg'] or 0

        # Calculate percentage
        if obj.target_value > 0:
            percentage = min(100, (float(current_value) / float(obj.target_value)) * 100)
        else:
            percentage = 0

        return {
            'current_value': float(current_value),
            'target_value': float(obj.target_value),
            'percentage': round(percentage, 1),
            'period_start': start.isoformat(),
            'period_end': end.isoformat()
        }

    def validate(self, attrs):
        """Validate goal dates and uniqueness."""
        start_date = attrs.get('start_date', timezone.now().date())
        end_date = attrs.get('end_date')
        
        if end_date and end_date < start_date:
            raise serializers.ValidationError({
                'end_date': "End date must be after start date."
            })
        
        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'username', 'email', 'date_of_birth', 'age',
            'height_cm', 'timezone', 'notifications_enabled',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'username', 'email', 'age', 'created_at', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Demonstrates password handling and related object creation.
    """
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': "Passwords do not match."
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        # Create associated profile
        UserProfile.objects.create(user=user)
        return user


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for nested representations."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined']
        read_only_fields = fields


class DashboardSerializer(serializers.Serializer):
    """
    Serializer for dashboard/summary data.
    Demonstrates non-model serializers.
    """
    total_metrics_logged = serializers.IntegerField()
    active_goals = serializers.IntegerField()
    metrics_this_week = serializers.IntegerField()
    goals_on_track = serializers.IntegerField()
    recent_metrics = HealthMetricSerializer(many=True)
    goal_progress = GoalSerializer(many=True)
