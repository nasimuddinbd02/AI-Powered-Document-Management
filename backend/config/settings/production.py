"""
Production settings for AI-Powered Document Management System.

Uses PostgreSQL, enforces security headers, and restricts CORS.
"""

from decouple import config

from .base import *  # noqa: F401, F403

# =============================================================================
# Debug Mode — NEVER True in production
# =============================================================================

DEBUG = False

# =============================================================================
# Database — PostgreSQL
# =============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="docmanager"),
        "USER": config("DB_USER", default="postgres"),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

# =============================================================================
# Security Settings
# =============================================================================

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"

# =============================================================================
# CORS — restrictive in production
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = False
# CORS_ALLOWED_ORIGINS is set in base.py from env

# =============================================================================
# Static Files — use whitenoise or cloud storage
# =============================================================================

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# =============================================================================
# Email — use SMTP in production
# =============================================================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")

# =============================================================================
# Logging — file-based in production
# =============================================================================

LOGGING["root"]["handlers"] = ["console", "file"]  # noqa: F405
LOGGING["loggers"]["django"]["handlers"] = ["console", "file"]  # noqa: F405
LOGGING["loggers"]["apps"]["handlers"] = ["console", "file"]  # noqa: F405
LOGGING["loggers"]["apps"]["level"] = "WARNING"  # noqa: F405
