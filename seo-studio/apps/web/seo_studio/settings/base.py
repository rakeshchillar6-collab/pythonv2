# seo_studio/settings/base.py
import os
from pathlib import Path
import environ
from datetime import timedelta
from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Initialize django-environ
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    CORS_ALLOWED_ORIGINS=(list, []),
    TIME_ZONE=(str, 'UTC'),
)

# For local development, read .env file
# In production, environment variables should be set directly.
environ.Env.read_env(os.path.join(BASE_DIR.parent, 'infra/env/.env'))

# --- Core Settings ---
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')
CSRF_TRUSTED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS') # Same as CORS for panel access

# --- Application Definitions ---
DJANGO_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'pgvector.django',
    'django_htmx',
    'drf_spectacular',
    'django_celery_beat',
]

LOCAL_APPS = [
    'common.apps.CommonConfig',
    'core.apps.CoreConfig',
    'editor.apps.EditorConfig',
    'integrations.apps.IntegrationsConfig',
    'content.apps.ContentConfig',
    'seo.apps.SeoConfig',
    'metaphorge.apps.MetaphorgeConfig',
    'reports.apps.ReportsConfig',
    'scheduler.apps.SchedulerConfig',
    'rum.apps.RumConfig',
    'adminui.apps.AdminuiConfig',
    'vectorsearch.apps.VectorsearchConfig',
    'apis.apps.ApisConfig',
    'calendar.apps.CalendarConfig',
    'graph.apps.GraphConfig',
    'seo_trends.apps.SeoTrendsConfig',
    'alerts.apps.AlertsConfig',
    'abtest.apps.AbtestConfig',

    # New SEO & Publishing apps
    'schema_builder.apps.SchemaBuilderConfig',
    'sitemap.apps.SitemapConfig',
    'robots.apps.RobotsConfig',
    'publishing.apps.PublishingConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# --- Middleware ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.SiteMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'abtest.middleware.ABTestMiddleware',
]

# --- URLs and Server ---
ROOT_URLCONF = 'seo_studio.urls'
WSGI_APPLICATION = 'seo_studio.wsgi.application'
ASGI_APPLICATION = 'seo_studio.asgi.application'

# --- Channel Layers ---
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env('REDIS_URL')],
        },
    },
}

# --- Templates ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# --- Database ---
DATABASES = {'default': env.db('DATABASE_URL')}
DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'

# --- Password and Auth ---
AUTH_USER_MODEL = 'core.User'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Internationalization ---
LANGUAGE_CODE = env('LANGUAGE_CODE', default='fa-ir')
TIME_ZONE = env('TIME_ZONE')
USE_I18N = True
USE_TZ = True

# --- Static and Media Files ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --- Primary Key ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- REST Framework ---
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser'],
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework_simplejwt.authentication.JWTAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_THROTTLING_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLING_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
}

# --- JWT Settings ---
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=env.int('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', 60)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=env.int('JWT_REFRESH_TOKEN_LIFETIME_DAYS', 7)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# --- CORS ---
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS')
CORS_ALLOW_CREDENTIALS = False # Recommended for JWT-based auth where tokens are sent in headers

# --- Celery ---
CELERY_BROKER_URL = env('REDIS_URL')
CELERY_RESULT_BACKEND = env('REDIS_URL')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SCHEDULE = {
    'publish-scheduled-posts-every-minute': {
        'task': 'content.tasks.publish_scheduled_posts',
        'schedule': crontab(), # Run every minute
    },
    'run-re-embedding-policy-hourly': {
        'task': 'vectorsearch.tasks.apply_reembedding_policy',
        'schedule': crontab(minute='0'), # Run every hour at minute 0
    },
    'maintain-vector-indexes-nightly': {
        'task': 'vectorsearch.tasks.maintain_indexes_task',
        'schedule': crontab(minute='0', hour='3'), # Run every night at 3 AM
    },
    'sync-gsc-properties-daily': {
        'task': 'integrations.tasks.sync_all_gsc_properties', # A wrapper task
        'schedule': crontab(minute='0', hour='4'), # Run every night at 4 AM
    },
    'detect-alerts-daily': {
        'task': 'alerts.tasks.detect_all_alerts',
        'schedule': crontab(minute='0', hour='5'), # Run every night at 5 AM
    },
}

# --- Logging ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(module)s %(funcName)s %(lineno)d %(message)s'
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json' if not DEBUG else 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# --- DRF Spectacular ---
SPECTACULAR_SETTINGS = {
    'TITLE': 'SEO Studio API',
    'DESCRIPTION': 'API documentation for the SEO Studio project.',
    'VERSION': '1.0.0',
}
