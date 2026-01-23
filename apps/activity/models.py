from __future__ import annotations

import uuid
from typing import Any

from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Tag(models.Model):
	uid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True, unique=True)
	name = models.CharField(max_length=64, db_index=True)
	color = models.CharField(max_length=16, blank=True)
	tags = models.JSONField(default=list, blank=True)
	created_at = models.DateTimeField(default=timezone.now, db_index=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["name"]
		constraints = [
			models.UniqueConstraint(fields=("name",), name="activity_tag_unique_name"),
		]

	def __str__(self) -> str:
		return self.name


class TaggedItem(models.Model):
	uid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True, unique=True)

	tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="tagged_items")
	content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
	object_id = models.CharField(max_length=64, db_index=True)
	content_object: Any = GenericForeignKey("content_type", "object_id")

	tags = models.JSONField(default=list, blank=True)
	created_at = models.DateTimeField(default=timezone.now, db_index=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		indexes = [
			models.Index(fields=["content_type", "object_id"], name="activity_ta_content_ebb53f_idx"),
			models.Index(fields=["tag", "created_at"], name="activity_ta_tag_id_33f4fd_idx"),
		]
		constraints = [
			models.UniqueConstraint(fields=("tag", "content_type", "object_id"), name="activity_taggeditem_unique"),
		]

	def __str__(self) -> str:
		return f"{self.tag} → {self.content_type_id}:{self.object_id}"


class Note(models.Model):
	uid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True, unique=True)

	content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
	object_id = models.CharField(max_length=64, db_index=True)
	content_object: Any = GenericForeignKey("content_type", "object_id")

	body = models.TextField()
	tags = models.JSONField(default=list, blank=True)

	actor_user_id = models.CharField(max_length=64, blank=True, db_index=True)
	actor_email = models.CharField(max_length=254, blank=True, db_index=True)
	request_id = models.CharField(max_length=64, blank=True, db_index=True)

	created_at = models.DateTimeField(default=timezone.now, db_index=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["content_type", "object_id", "created_at"], name="activity_no_content_d5e855_idx"),
		]

	def __str__(self) -> str:
		return f"Note({self.uid})"


class ActivityEvent(models.Model):
	uid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True, unique=True)

	verb = models.CharField(max_length=64, db_index=True)
	message = models.CharField(max_length=500, blank=True)
	metadata = models.JSONField(default=dict, blank=True)
	tags = models.JSONField(default=list, blank=True)

	content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
	object_id = models.CharField(max_length=64, db_index=True)
	content_object: Any = GenericForeignKey("content_type", "object_id")

	actor_user_id = models.CharField(max_length=64, blank=True, db_index=True)
	actor_email = models.CharField(max_length=254, blank=True, db_index=True)
	request_id = models.CharField(max_length=64, blank=True, db_index=True)

	created_at = models.DateTimeField(default=timezone.now, db_index=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["verb", "created_at"], name="activity_ac_verb_a59b5b_idx"),
			models.Index(fields=["content_type", "object_id", "created_at"], name="activity_ac_content_2d854f_idx"),
		]

	def __str__(self) -> str:
		return f"{self.verb} ({self.created_at:%Y-%m-%d %H:%M:%S})"

