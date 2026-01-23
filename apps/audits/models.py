from __future__ import annotations

import uuid

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class AuditStatus(models.TextChoices):
	SUCCESS = "success", "Success"
	FAILURE = "failure", "Failure"


class AuditEventQuerySet(models.QuerySet):
	def hard_delete(self):
		"""
		Bypass model.delete() / signals. Intended for retention purges.
		"""
		return self._raw_delete(self.db)


class AuditEventManager(models.Manager.from_queryset(AuditEventQuerySet)):
	pass


class AuditEvent(models.Model):
	"""
	Stored per schema:
	  - In public schema: platform/control-plane audit events
	  - In tenant schemas: tenant/user/business audit events
	"""
	
	created_at = models.DateTimeField(default=timezone.now, db_index=True)
	updated_at = models.DateTimeField(auto_now=True)
	tags = models.JSONField(default=list, blank=True)
	event_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
	
	# Correlation / tracing
	request_id = models.CharField(max_length=64, blank=True, db_index=True)
	tenant_schema = models.CharField(max_length=63, blank=True, db_index=True)
	
	# Actor
	actor_user_id = models.CharField(max_length=64, blank=True, db_index=True)
	actor_email = models.CharField(max_length=254, blank=True, db_index=True)
	
	# Request context
	request_method = models.CharField(max_length=10, blank=True)
	request_path = models.CharField(max_length=300, blank=True)
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
	
	objects = AuditEventManager()
	
	class Meta:
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["action", "created_at"]),
			models.Index(fields=["actor_email", "created_at"]),
			models.Index(fields=["object_type", "object_id"]),
		]
	
	def __str__(self) -> str:
		return f"[{self.created_at:%Y-%m-%d %H:%M:%S}] {self.action} ({self.status})"

	def save(self, *args, **kwargs):
		# Treat audit logs as append-only.
		if self.pk is not None:
			raise ValidationError("AuditEvent is immutable (append-only).")
		return super().save(*args, **kwargs)

	def delete(self, *args, **kwargs):
		# Use AuditEvent.objects.filter(...).hard_delete() for retention purges.
		raise ValidationError("AuditEvent cannot be deleted via ORM delete().")