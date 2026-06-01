"""
Celery application for AI-Powered Document Management System.

Configures Celery to auto-discover tasks from all installed apps.
"""

import os

from celery import Celery

# Set default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("docmanager")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task that prints its own request info."""
    print(f"Request: {self.request!r}")
