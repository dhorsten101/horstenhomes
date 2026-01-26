from __future__ import annotations

import os

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStampedUUIDModel


def _document_upload_to(instance: Document, filename: str) -> str:
	base, ext = os.path.splitext(filename)
	safe_base = slugify(base)[:80] or "document"
	return f"documents/{instance.content_type.app_label}/{instance.content_type.model}/{instance.object_id}/{safe_base}{ext.lower()}"


class Document(TimeStampedUUIDModel):
	"""
	A file attached to a business object (tenant schema).
	"""

	content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
	object_id = models.PositiveBigIntegerField(db_index=True)
	content_object = GenericForeignKey("content_type", "object_id")

	title = models.CharField(max_length=200, blank=True)
	description = models.TextField(blank=True)

	file = models.FileField(upload_to=_document_upload_to)
	uploaded_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="uploaded_documents",
	)

	class Meta:
		indexes = [
			models.Index(fields=["content_type", "object_id", "created_at"]),
		]

	def __str__(self) -> str:
		return self.title or f"Document {self.pk}"
