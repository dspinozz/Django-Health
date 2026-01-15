"""
Django REST Framework Views

Demonstrates DRF view patterns:
- ViewSets for CRUD operations
- Custom actions with @action decorator
- Filtering, searching, and ordering
- Permission handling
- Custom response data
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from django.db.models import Avg, Sum, Count, Min, Max
from django.utils import timezone
from datetime import timedelta

from .models import MetricType, HealthMetric, Goal, UserProfile
from .serializers import (
    MetricTypeSerializer,
    HealthMetricSerializer,
    HealthMetricCreateSerializer,
    GoalSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)


class MetricTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for MetricType CRUD operations.
    """
    queryset = MetricType.objects.filter(is_active=True)
    serializer_class = MetricTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class HealthMetricViewSet(viewsets.ModelViewSet):
    """
    ViewSet for HealthMetric CRUD operations.
    Users can only access their own metrics.
    """
    serializer_class = HealthMetricSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['metric_type', 'recorded_date']
    search_fields = ['notes']
    ordering_fields = ['recorded_date', 'value', 'created_at']
    ordering = ['-recorded_date']

    def get_queryset(self):
        """Return only the current user's metrics."""
        return HealthMetric.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Use different serializers for create/update vs read."""
        if self.action in ['create', 'update', 'partial_update']:
            return HealthMetricCreateSerializer
        return HealthMetricSerializer

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get summary statistics for the user's metrics.
        
        Query params:
        - days: Number of days to include (default: 7)
        - metric_type: Filter by specific metric type ID
        """
        days = int(request.query_params.get('days', 7))
        metric_type_id = request.query_params.get('metric_type')
        
        start_date = timezone.now().date() - timedelta(days=days)
        queryset = self.get_queryset().filter(recorded_date__gte=start_date)
        
        if metric_type_id:
            queryset = queryset.filter(metric_type_id=metric_type_id)

        summary = queryset.values('metric_type__name', 'metric_type__unit').annotate(
            count=Count('id'),
            average=Avg('value'),
            total=Sum('value'),
            min_value=Min('value'),
            max_value=Max('value')
        )

        return Response({
            'period_start': start_date.isoformat(),
            'period_end': timezone.now().date().isoformat(),
            'metrics': list(summary)
        })

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """
        Get daily trends for a specific metric type.
        
        Query params:
        - metric_type: Metric type ID (required)
        - days: Number of days (default: 30)
        """
        metric_type_id = request.query_params.get('metric_type')
        if not metric_type_id:
            return Response(
                {'error': 'metric_type parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)

        metrics = self.get_queryset().filter(
            metric_type_id=metric_type_id,
            recorded_date__gte=start_date
        ).order_by('recorded_date')

        data = [
            {'date': m.recorded_date.isoformat(), 'value': float(m.value)}
            for m in metrics
        ]

        return Response({
            'metric_type_id': metric_type_id,
            'period_start': start_date.isoformat(),
            'period_end': timezone.now().date().isoformat(),
            'data_points': data
        })


class GoalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Goal CRUD operations.
    Users can only access their own goals.
    """
    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['metric_type', 'goal_type', 'is_active']
    ordering_fields = ['created_at', 'target_value']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return only the current user's goals."""
        return Goal.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a goal without deleting it."""
        goal = self.get_object()
        goal.is_active = False
        goal.save()
        return Response({'status': 'Goal deactivated'})

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active, non-expired goals."""
        today = timezone.now().date()
        active_goals = self.get_queryset().filter(is_active=True).exclude(end_date__lt=today)
        serializer = self.get_serializer(active_goals, many=True)
        return Response(serializer.data)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user profile management.
    Users can only access their own profile.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only the current user's profile."""
        return UserProfile.objects.filter(user=self.request.user)

    def get_object(self):
        """Get or create the user's profile."""
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def list(self, request):
        """Return the current user's profile."""
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)


class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet for authentication operations.
    """
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def register(self, request):
        """Register a new user account."""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'user': UserSerializer(user).data,
                'token': token.key,
                'message': 'Registration successful'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Logout and invalidate the token."""
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
        return Response({'message': 'Logged out successfully'})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user information."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for dashboard/summary data.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Get dashboard summary data for the current user."""
        user = request.user
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        total_metrics = HealthMetric.objects.filter(user=user).count()
        metrics_this_week = HealthMetric.objects.filter(
            user=user, recorded_date__gte=week_ago
        ).count()
        
        active_goals = Goal.objects.filter(
            user=user, is_active=True
        ).exclude(end_date__lt=today)
        
        recent_metrics = HealthMetric.objects.filter(
            user=user
        ).order_by('-recorded_date', '-created_at')[:5]

        # Calculate goals on track (>= 50% progress)
        goals_on_track = 0
        goal_serializer = GoalSerializer(
            active_goals, many=True, context={'request': request}
        )
        for goal_data in goal_serializer.data:
            if goal_data.get('progress', {}).get('percentage', 0) >= 50:
                goals_on_track += 1

        return Response({
            'total_metrics_logged': total_metrics,
            'active_goals': active_goals.count(),
            'metrics_this_week': metrics_this_week,
            'goals_on_track': goals_on_track,
            'recent_metrics': HealthMetricSerializer(
                recent_metrics, many=True, context={'request': request}
            ).data,
            'goal_progress': goal_serializer.data
        })
