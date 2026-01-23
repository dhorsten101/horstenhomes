from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class TimeStampedUUIDModel(models.Model):
	"""
	Abstract base model:
	- uid: stable external identifier (UUID)
	- created_at / updated_at timestamps

	We keep the default integer PK for safety and add a UUID separately.
	"""

	uid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
	tags = models.JSONField(default=list, blank=True)
	created_at = models.DateTimeField(default=timezone.now, db_index=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True
