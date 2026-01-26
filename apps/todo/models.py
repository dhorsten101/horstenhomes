from __future__ import annotations

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedUUIDModel


class TodoStatus(models.TextChoices):
	OPEN = "open", "Open"
	DONE = "done", "Done"


class TodoItem(TimeStampedUUIDModel):
	"""
	A to-do item optionally attached to a business object (tenant schema).
	"""

	content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
	object_id = models.PositiveBigIntegerField(null=True, blank=True, db_index=True)
	content_object = GenericForeignKey("content_type", "object_id")

	title = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	status = models.CharField(max_length=10, choices=TodoStatus.choices, default=TodoStatus.OPEN, db_index=True)
	due_date = models.DateField(null=True, blank=True, db_index=True)
	completed_at = models.DateTimeField(null=True, blank=True)

	assigned_to = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="todos_assigned",
	)
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="todos_created",
	)

	class Meta:
		indexes = [
			models.Index(fields=["content_type", "object_id", "status", "created_at"]),
			# Global todo lists are usually filtered by status + time
			models.Index(fields=["status", "created_at"]),
		]

	def mark_done(self):
		self.status = TodoStatus.DONE
		self.completed_at = timezone.now()

	def reopen(self):
		self.status = TodoStatus.OPEN
		self.completed_at = None

	def __str__(self) -> str:
		return self.title
