from django.core.validators import RegexValidator
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.contrib.contenttypes.fields import GenericRelation

from apps.core.models import TimeStampedUUIDModel

class TenantStatus(models.TextChoices):
	PENDING = "pending", "Pending"
	PROVISIONING = "provisioning", "Provisioning"
	ACTIVE = "active", "Active"
	SUSPENDED = "suspended", "Suspended"
	FAILED = "failed", "Failed"


slug_validator = RegexValidator(
	regex=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
	message="Slug must be lowercase letters, numbers, and hyphens only.",
)


class Tenant(TimeStampedUUIDModel, TenantMixin):
	"""
	Stored in PUBLIC schema. Each row represents a tenant and owns a DB schema.
	"""
	name = models.CharField(max_length=200)
	slug = models.SlugField(unique=True)
	
	status = models.CharField(
		max_length=20,
		choices=TenantStatus.choices,
		default=TenantStatus.PENDING,
		db_index=True,
	)

	# django-tenants will create the schema automatically when saving the tenant
	auto_create_schema = True

	tag_items = GenericRelation("activity.TaggedItem", content_type_field="content_type", object_id_field="object_id")
	note_items = GenericRelation("activity.Note", content_type_field="content_type", object_id_field="object_id")
	activity_events = GenericRelation("activity.ActivityEvent", content_type_field="content_type", object_id_field="object_id")
	
	external_id = models.CharField(max_length=120, blank=True, db_index=True)
	source = models.CharField(max_length=80, blank=True)  # "manual", "csv", "api:xyz"


	def save(self, *args, **kwargs):
		self.slug = (self.slug or "").lower()
		
		# Only set schema_name for non-public tenants when schema_name is blank
		if not self.schema_name:
			self.schema_name = self.slug
		
		super().save(*args, **kwargs)
	
	def __str__(self) -> str:
		return f"{self.name} ({self.schema_name})"


class Domain(TimeStampedUUIDModel, DomainMixin):
	"""
	Stored in PUBLIC schema. Maps hostnames to tenants.
	"""
	tag_items = GenericRelation("activity.TaggedItem", content_type_field="content_type", object_id_field="object_id")
	note_items = GenericRelation("activity.Note", content_type_field="content_type", object_id_field="object_id")
	activity_events = GenericRelation("activity.ActivityEvent", content_type_field="content_type", object_id_field="object_id")