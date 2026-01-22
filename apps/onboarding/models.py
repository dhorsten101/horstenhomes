from django.db import models


class TenantRequestStatus(models.TextChoices):
	NEW = "new", "New"
	CONTACTED = "contacted", "Contacted"
	APPROVED = "approved", "Approved"
	PROVISIONED = "provisioned", "Provisioned"
	REJECTED = "rejected", "Rejected"


class TenantRequest(models.Model):
	company_name = models.CharField(max_length=200)
	desired_slug = models.SlugField(blank=True)
	
	contact_name = models.CharField(max_length=120)
	contact_email = models.EmailField()
	contact_phone = models.CharField(max_length=40, blank=True)
	
	# Email to be used for the initial tenant admin user (created in the tenant schema).
	# Stored in public schema only as part of the onboarding request workflow.
	admin_email = models.EmailField(blank=True)
	
	notes = models.TextField(blank=True)
	
	status = models.CharField(
		max_length=20,
		choices=TenantRequestStatus.choices,
		default=TenantRequestStatus.NEW,
		db_index=True,
	)
	
	converted_tenant_schema = models.CharField(max_length=63, blank=True)
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	def __str__(self):
		return f"{self.company_name} ({self.status})"