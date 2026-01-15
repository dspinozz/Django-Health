# 🏥 Django Health Metrics API

A RESTful API built with Django REST Framework for tracking personal health metrics, setting goals, and monitoring progress over time.

## Features

- **🔐 Token Authentication** - Secure user registration and login with token-based auth
- **📊 Health Metrics Tracking** - Log daily metrics like steps, sleep, water intake, weight, heart rate
- **🎯 Goal Management** - Set daily, weekly, or monthly goals with automatic progress tracking
- **📈 Analytics** - Summary statistics, trends, and dashboard endpoints
- **👤 User Profiles** - Extended user profiles with health-related settings
- **🔍 Filtering & Search** - Built-in filtering, searching, and ordering on all endpoints
- **📄 Pagination** - Configurable pagination (default: 20 items/page)
- **⏱️ Rate Limiting** - Throttling for API protection (100/hour anon, 1000/hour authenticated)

## Tech Stack

- **Python 3.11+**
- **Django 5.2**
- **Django REST Framework 3.16**
- **SQLite** (development) / **PostgreSQL** (production ready)
- **Token Authentication**

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/django-health-metrics-api.git
cd django-health-metrics-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register/` | Register new user |
| POST | `/api/v1/auth/token/` | Get auth token (login) |
| POST | `/api/v1/auth/logout/` | Invalidate token |
| GET | `/api/v1/auth/me/` | Get current user |

### Metric Types

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/metric-types/` | List all metric types |
| POST | `/api/v1/metric-types/` | Create metric type |
| GET | `/api/v1/metric-types/{id}/` | Get metric type |
| PUT/PATCH | `/api/v1/metric-types/{id}/` | Update metric type |
| DELETE | `/api/v1/metric-types/{id}/` | Delete metric type |

### Health Metrics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/metrics/` | List user's metrics |
| POST | `/api/v1/metrics/` | Create metric entry |
| GET | `/api/v1/metrics/{id}/` | Get metric entry |
| PUT/PATCH | `/api/v1/metrics/{id}/` | Update metric entry |
| DELETE | `/api/v1/metrics/{id}/` | Delete metric entry |
| GET | `/api/v1/metrics/summary/` | Get summary statistics |
| GET | `/api/v1/metrics/trends/` | Get metric trends |

### Goals

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/goals/` | List user's goals |
| POST | `/api/v1/goals/` | Create goal |
| GET | `/api/v1/goals/{id}/` | Get goal with progress |
| PUT/PATCH | `/api/v1/goals/{id}/` | Update goal |
| DELETE | `/api/v1/goals/{id}/` | Delete goal |
| POST | `/api/v1/goals/{id}/deactivate/` | Deactivate goal |
| GET | `/api/v1/goals/active/` | List active goals |

### Dashboard & Profile

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/dashboard/` | Get dashboard summary |
| GET | `/api/v1/profile/` | Get user profile |
| PATCH | `/api/v1/profile/{id}/` | Update profile |

## Usage Examples

### Register a new user

```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }'
```

### Log a health metric

```bash
curl -X POST http://localhost:8000/api/v1/metrics/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "metric_type": 1,
    "value": "10000",
    "recorded_date": "2026-01-15",
    "notes": "Great day for walking!"
  }'
```

### Create a goal

```bash
curl -X POST http://localhost:8000/api/v1/goals/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "metric_type_id": 1,
    "target_value": "10000",
    "goal_type": "DAILY",
    "direction": "INCREASE"
  }'
```

### Get dashboard

```bash
curl http://localhost:8000/api/v1/dashboard/ \
  -H "Authorization: Token YOUR_TOKEN"
```

## Data Models

### MetricType
Pre-configured metric types with validation bounds:
- `steps` (0 - 100,000)
- `sleep_hours` (0 - 24)
- `water_intake` (0 - 10,000 ml)
- `weight` (20 - 500 kg)
- `heart_rate` (30 - 220 bpm)
- `calories_burned` (0 - 10,000 kcal)

### HealthMetric
Daily metric entries with:
- User association
- Metric type reference
- Value with validation
- Recorded date (unique per user/type/day)
- Optional notes

### Goal
User goals with:
- Goal types: `DAILY`, `WEEKLY`, `MONTHLY`
- Directions: `INCREASE`, `DECREASE`, `MAINTAIN`
- Automatic progress calculation
- Active/expired status tracking

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | Dev key |
| `DEBUG` | Enable debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost,127.0.0.1` |
| `DATABASE_URL` | PostgreSQL URL | SQLite |

## Running Tests

```bash
python manage.py test metrics -v2
```

## Project Structure

```
django-health-metrics-api/
├── config/                 # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── metrics/               # Health metrics app
│   ├── models.py          # Data models
│   ├── serializers.py     # DRF serializers
│   ├── views.py           # ViewSets
│   ├── urls.py            # API routing
│   ├── admin.py           # Admin config
│   └── tests.py           # Test cases
├── requirements.txt
├── manage.py
└── README.md
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
