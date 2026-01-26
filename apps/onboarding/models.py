from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from apps.core.models import TimeStampedUUIDModel


class TenantRequestStatus(models.TextChoices):
	NEW = "new", "New"
	CONTACTED = "contacted", "Contacted"
	APPROVED = "approved", "Approved"
	PROVISIONED = "provisioned", "Provisioned"
	REJECTED = "rejected", "Rejected"


class TenantRequest(TimeStampedUUIDModel):
	company_name = models.CharField(max_length=200)
	desired_slug = models.SlugField(blank=True)
	
	contact_name = models.CharField(max_length=120)
	contact_first_name = models.CharField(max_length=120, blank=True)
	contact_last_name = models.CharField(max_length=120, blank=True)
	contact_email = models.EmailField()
	contact_phone = models.CharField(max_length=40, blank=True)
	
	# Email to be used for the initial tenant admin user (created in the tenant schema).
	# Stored in public schema only as part of the onboarding request workflow.
	admin_email = models.EmailField(blank=True)
	
	notes = models.TextField(blank=True)

	tag_items = GenericRelation("activity.TaggedItem", content_type_field="content_type", object_id_field="object_id")
	note_items = GenericRelation("activity.Note", content_type_field="content_type", object_id_field="object_id")
	activity_events = GenericRelation("activity.ActivityEvent", content_type_field="content_type", object_id_field="object_id")
	
	status = models.CharField(
		max_length=20,
		choices=TenantRequestStatus.choices,
		default=TenantRequestStatus.NEW,
		db_index=True,
	)
	
	converted_tenant_schema = models.CharField(max_length=63, blank=True)
	requested_plan_code = models.SlugField(default="free", blank=True)

	# Provisioning outputs (public schema only; used to give the requester a seamless next step)
	provisioned_domain = models.CharField(max_length=255, blank=True)
	reset_uidb64 = models.CharField(max_length=255, blank=True)
	reset_token = models.CharField(max_length=255, blank=True)

	class Meta:
		indexes = [
			models.Index(fields=["status", "created_at"]),
		]
	
	def __str__(self):
		return f"{self.company_name} ({self.status})"