from django.contrib import admin, messages
from django.utils import timezone

from apps.onboarding.models import TenantRequest, TenantRequestStatus
from apps.tenancy.models import Tenant, Domain, TenantStatus
from apps.tenancy.services.onboarding import provision_tenant  # your existing service

DEFAULT_BASE_DOMAIN = "horstenhomes.local"  # dev; use env in prod

@admin.register(TenantRequest)
class TenantRequestAdmin(admin.ModelAdmin):
	list_display = ("company_name", "contact_email", "desired_slug", "status", "created_at")
	list_filter = ("status",)
	search_fields = ("company_name", "contact_email", "desired_slug")
	ordering = ("-created_at",)
	actions = ("action_approve_and_provision",)
	
	@admin.action(description="Approve + Provision (create tenant + domain + migrate)")
	def action_approve_and_provision(self, request, queryset):
		for tr in queryset:
			if tr.status in (TenantRequestStatus.PROVISIONED, TenantRequestStatus.REJECTED):
				self.message_user(request, f"Skipping {tr.company_name} (status={tr.status})", level=messages.WARNING)
				continue
			
			slug = (tr.desired_slug or "").strip().lower()
			if not slug:
				self.message_user(request, f"{tr.company_name}: missing desired_slug", level=messages.ERROR)
				continue
			
			# Create tenant
			try:
				tenant = Tenant.objects.create(
					name=tr.company_name,
					slug=slug,
					status=TenantStatus.PROVISIONING,
					schema_name=slug,  # explicit
				)
			except Exception as e:
				self.message_user(request, f"{tr.company_name}: tenant create failed: {e}", level=messages.ERROR)
				continue
			
			# Create domain
			domain = f"{slug}.{DEFAULT_BASE_DOMAIN}"
			Domain.objects.get_or_create(domain=domain, tenant=tenant, defaults={"is_primary": True})
			
			# Provision schema + migrate + create tenant superuser inside your service
			try:
				provision_tenant(tenant=tenant, admin_email=tr.contact_email)
				tenant.status = TenantStatus.ACTIVE
				tenant.save(update_fields=["status"])
				
				tr.status = TenantRequestStatus.PROVISIONED
				tr.converted_tenant_schema = tenant.schema_name
				tr.updated_at = timezone.now()
				tr.save(update_fields=["status", "converted_tenant_schema", "updated_at"])
				
				self.message_user(
					request,
					f"Provisioned {tr.company_name}: {domain}",
					level=messages.SUCCESS,
				)
			except Exception as e:
				tenant.status = TenantStatus.FAILED
				tenant.save(update_fields=["status"])
				self.message_user(request, f"FAILED provisioning {tr.company_name}: {e}", level=messages.ERROR)