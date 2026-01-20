from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Tenant(TenantMixin):
	"""
	Stored in PUBLIC schema. Each row represents a tenant and owns a DB schema.
	"""
	name = models.CharField(max_length=200)
	slug = models.SlugField(unique=True)
	
	# django-tenants will create the schema automatically when saving the tenant
	auto_create_schema = True
	
	def __str__(self) -> str:
		return f"{self.name} ({self.schema_name})"


class Domain(DomainMixin):
	"""
	Stored in PUBLIC schema. Maps hostnames to tenants.
	"""
	pass