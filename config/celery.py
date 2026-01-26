from __future__ import annotations

import os

from celery import Celery

# Default Django settings module for `celery` CLI.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("horstenhomes")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

