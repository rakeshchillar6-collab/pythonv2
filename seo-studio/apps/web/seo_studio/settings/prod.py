# seo_studio/settings/prod.py
from .base import *

# Override base settings for production

DEBUG = False

# Security settings for production
# Ensure these are set in your environment variables for production
# ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')
# CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# More robust password hashing for production
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# Logging level for production
LOGGING['root']['level'] = 'INFO'
