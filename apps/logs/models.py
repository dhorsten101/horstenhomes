from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class LogLevel(models.TextChoices):
	DEBUG = "DEBUG", "DEBUG"
	INFO = "INFO", "INFO"
	WARNING = "WARNING", "WARNING"
	ERROR = "ERROR", "ERROR"
	CRITICAL = "CRITICAL", "CRITICAL"


class LogEntry(models.Model):
	"""
	Stored per schema:
	  - public schema: platform/control-plane runtime logs
	  - tenant schemas: tenant runtime logs
	"""

	uid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True, unique=True)
	created_at = models.DateTimeField(default=timezone.now, db_index=True)
	level = models.CharField(max_length=10, choices=LogLevel.choices, db_index=True)
	logger = models.CharField(max_length=200, db_index=True)
	message = models.TextField()

	# Code location
	pathname = models.CharField(max_length=500, blank=True)
	lineno = models.IntegerField(null=True, blank=True)
	func_name = models.CharField(max_length=200, blank=True)
	module = models.CharField(max_length=200, blank=True)

	# Process/thread
	process = models.BigIntegerField(null=True, blank=True)
	thread = models.BigIntegerField(null=True, blank=True)

	# Exception info
	exc_text = models.TextField(blank=True)

	# Request context (best-effort; uses audit context when available)
	request_id = models.CharField(max_length=64, blank=True, db_index=True)
	tenant_schema = models.CharField(max_length=63, blank=True, db_index=True)
	request_method = models.CharField(max_length=10, blank=True)
	request_path = models.CharField(max_length=300, blank=True)
	actor_user_id = models.CharField(max_length=64, blank=True, db_index=True)
	actor_email = models.CharField(max_length=254, blank=True, db_index=True)
	ip_address = models.GenericIPAddressField(null=True, blank=True)
	user_agent = models.TextField(blank=True)

	# Extra structured data
	extra = models.JSONField(default=dict, blank=True)

	class Meta:
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["level", "created_at"]),
			models.Index(fields=["logger", "created_at"]),
			models.Index(fields=["tenant_schema", "created_at"]),
			models.Index(fields=["request_id"]),
		]

	def __str__(self) -> str:
		return f"[{self.created_at:%Y-%m-%d %H:%M:%S}] {self.level} {self.logger}: {self.message[:120]}"
