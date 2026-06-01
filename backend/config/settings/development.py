"""
Development settings for AI-Powered Document Management System.

Uses SQLite for quick development and enables debug tools.
"""

from .base import *  # noqa: F401, F403

# =============================================================================
# Debug Mode
# =============================================================================

DEBUG = True

# Disable strict password validation for easy local testing
AUTH_PASSWORD_VALIDATORS = []

# =============================================================================
# Database — SQLite for quick local development
# =============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# =============================================================================
# CORS — allow all in development
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = True

# =============================================================================
# Email — console backend for development
# =============================================================================

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# =============================================================================
# Additional renderer for browsable API during development
# =============================================================================

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)

# =============================================================================
# Throttle rates — more generous in development
# =============================================================================

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "100/minute",
    "user": "500/minute",
}

# =============================================================================
# Logging — more verbose in development
# =============================================================================

LOGGING["loggers"]["apps"]["level"] = "DEBUG"  # noqa: F405
