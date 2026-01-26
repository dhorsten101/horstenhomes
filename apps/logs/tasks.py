from __future__ import annotations

from celery import shared_task
from django.core.management import call_command


@shared_task
def purge_audit_events_task(days: int = 90) -> None:
	"""
	Example periodic job: purge old audit events.
	Run via Celery Beat schedule.
	"""
	call_command("purge_audit_events", days=days)

