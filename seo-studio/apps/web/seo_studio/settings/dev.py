# seo_studio/settings/dev.py
from .base import *

# Override base settings for development

DEBUG = True

# Add any development-specific settings here
# For example, enabling debug toolbar if installed
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1']

# For development, allow all hosts
ALLOWED_HOSTS = ["*"]

# Use console for email backend during development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# In development, it's okay to have a simpler password hasher for performance
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Logging level for development
LOGGING['root']['level'] = 'DEBUG'
