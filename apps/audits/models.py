from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class AuditStatus(models.TextChoices):
	SUCCESS = "success", "Success"
	FAILURE = "failure", "Failure"


class AuditEvent(models.Model):
	"""
	Stored per schema:
	  - In public schema: platform/control-plane audit events
	  - In tenant schemas: tenant/user/business audit events
	"""
	
	created_at = models.DateTimeField(default=timezone.now, db_index=True)
	
	# Correlation / tracing
	request_id = models.CharField(max_length=64, blank=True, db_index=True)
	tenant_schema = models.CharField(max_length=63, blank=True, db_index=True)
	
	# Actor
	actor_user_id = models.CharField(max_length=64, blank=True, db_index=True)
	actor_email = models.CharField(max_length=254, blank=True, db_index=True)
	
	# Request context
	ip_address = models.GenericIPAddressField(null=True, blank=True)
	user_agent = models.TextField(blank=True)
	
	# What happened
	action = models.CharField(max_length=128, db_index=True)  # e.g. "tenant.provisioned", "user.created"
	status = models.CharField(max_length=16, choices=AuditStatus.choices, default=AuditStatus.SUCCESS, db_index=True)
	message = models.CharField(max_length=500, blank=True)
	
	# Target object info (don’t force FK)
	object_type = models.CharField(max_length=128, blank=True, db_index=True)  # e.g. "tenancy.Tenant"
	object_id = models.CharField(max_length=64, blank=True, db_index=True)
	object_repr = models.CharField(max_length=300, blank=True)
	
	# Details
	changes = models.JSONField(default=dict, blank=True)   # {"field": {"from": x, "to": y}, ...}
	metadata = models.JSONField(default=dict, blank=True)  # extra context
	
	class Meta:
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["action", "created_at"]),
			models.Index(fields=["actor_email", "created_at"]),
			models.Index(fields=["object_type", "object_id"]),
		]
	
	def __str__(self) -> str:
		return f"[{self.created_at:%Y-%m-%d %H:%M:%S}] {self.action} ({self.status})"