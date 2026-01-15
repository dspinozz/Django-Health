"""
Tests for Health Metrics API.

Basic test coverage for models, serializers, and API endpoints.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from decimal import Decimal
from datetime import date

from .models import MetricType, HealthMetric, Goal, UserProfile


class MetricTypeModelTest(TestCase):
    """Tests for MetricType model."""

    def test_create_metric_type(self):
        """Test creating a metric type."""
        metric_type = MetricType.objects.create(
            name='test_steps',
            unit='steps',
            description='Test step count',
            min_value=0,
            max_value=100000
        )
        self.assertEqual(str(metric_type), 'test_steps (steps)')
        self.assertTrue(metric_type.is_active)


class HealthMetricModelTest(TestCase):
    """Tests for HealthMetric model."""

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'testpass')
        self.metric_type = MetricType.objects.create(name='steps', unit='steps')

    def test_create_health_metric(self):
        """Test creating a health metric."""
        metric = HealthMetric.objects.create(
            user=self.user,
            metric_type=self.metric_type,
            value=Decimal('5000'),
            recorded_date=date.today()
        )
        self.assertEqual(metric.user, self.user)
        self.assertEqual(metric.value, Decimal('5000'))


class APIAuthenticationTest(APITestCase):
    """Tests for API authentication."""

    def test_register_user(self):
        """Test user registration endpoint."""
        response = self.client.post('/api/v1/auth/register/', {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied."""
        response = self.client.get('/api/v1/metrics/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MetricTypeAPITest(APITestCase):
    """Tests for MetricType API endpoints."""

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'testpass')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.metric_type = MetricType.objects.create(name='steps', unit='steps')

    def test_list_metric_types(self):
        """Test listing metric types."""
        response = self.client.get('/api/v1/metric-types/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_create_metric_type(self):
        """Test creating a metric type."""
        response = self.client.post('/api/v1/metric-types/', {
            'name': 'sleep',
            'unit': 'hours',
            'description': 'Sleep hours'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class HealthMetricAPITest(APITestCase):
    """Tests for HealthMetric API endpoints."""

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'testpass')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.metric_type = MetricType.objects.create(name='steps', unit='steps')

    def test_create_health_metric(self):
        """Test creating a health metric."""
        response = self.client.post('/api/v1/metrics/', {
            'metric_type': self.metric_type.id,
            'value': '8000',
            'recorded_date': date.today().isoformat()
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_own_metrics_only(self):
        """Test that users can only see their own metrics."""
        # Create metric for this user
        HealthMetric.objects.create(
            user=self.user,
            metric_type=self.metric_type,
            value=5000,
            recorded_date=date.today()
        )
        # Create another user with metric
        other_user = User.objects.create_user('other', 'other@test.com', 'pass')
        HealthMetric.objects.create(
            user=other_user,
            metric_type=self.metric_type,
            value=3000,
            recorded_date=date.today()
        )
        
        response = self.client.get('/api/v1/metrics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)


class GoalAPITest(APITestCase):
    """Tests for Goal API endpoints."""

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'testpass')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.metric_type = MetricType.objects.create(name='steps', unit='steps')

    def test_create_goal(self):
        """Test creating a goal."""
        response = self.client.post('/api/v1/goals/', {
            'metric_type_id': self.metric_type.id,
            'target_value': '10000',
            'goal_type': 'DAILY',
            'direction': 'INCREASE'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_deactivate_goal(self):
        """Test deactivating a goal."""
        goal = Goal.objects.create(
            user=self.user,
            metric_type=self.metric_type,
            target_value=10000,
            goal_type='DAILY'
        )
        response = self.client.post(f'/api/v1/goals/{goal.id}/deactivate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertFalse(goal.is_active)


class DashboardAPITest(APITestCase):
    """Tests for Dashboard API endpoint."""

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'testpass')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_dashboard_returns_data(self):
        """Test dashboard endpoint returns expected fields."""
        response = self.client.get('/api/v1/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_metrics_logged', response.data)
        self.assertIn('active_goals', response.data)
        self.assertIn('metrics_this_week', response.data)
