from django.contrib import admin, messages

from apps.audits.admin_mixins import AdminAuditMixin
from apps.audits.services import audit_log
from apps.tenancy.models import Tenant, Domain, TenantStatus
from apps.tenancy.services.onboarding import provision_tenant, suspend_tenant, activate_tenant


class TenantAdmin(AdminAuditMixin):
	audit_action_prefix = "admin.tenant"
	
	list_display = ("name", "slug", "schema_name", "status", "created_at")
	search_fields = ("name", "slug", "schema_name")
	list_filter = ("status",)
	actions = ("action_provision", "action_suspend", "action_activate")
	
	@admin.action(description="Provision selected tenants (create schema + migrate)")
	def action_provision(self, request, queryset):
		for t in queryset:
			try:
				audit_log(action="tenant.provision.started", obj=t)
				
				provision_tenant(tenant=t)
				
				audit_log(
					action="tenant.provision.completed",
					obj=t,
					metadata={
						"domains": list(t.domains.values_list("domain", flat=True)),
						"schema": t.schema_name,
					},
				)
				
				self.message_user(request, f"Provisioned: {t.slug}", level=messages.SUCCESS)
			
			except Exception as e:
				t.status = TenantStatus.FAILED
				t.save(update_fields=["status"])
				
				audit_log(
					action="tenant.provision.failed",
					obj=t,
					status="failure",
					message=str(e),
				)
				
				self.message_user(request, f"FAILED: {t.slug} → {e}", level=messages.ERROR)
	
	@admin.action(description="Suspend selected tenants")
	def action_suspend(self, request, queryset):
		for t in queryset:
			suspend_tenant(tenant=t)
			audit_log(action="tenant.suspended", obj=t)
		self.message_user(request, "Suspended selected tenants.", level=messages.SUCCESS)
	
	@admin.action(description="Activate selected tenants")
	def action_activate(self, request, queryset):
		for t in queryset:
			activate_tenant(tenant=t)
			audit_log(action="tenant.activated", obj=t)
		self.message_user(request, "Activated selected tenants.", level=messages.SUCCESS)


class DomainAdmin(AdminAuditMixin):
	audit_action_prefix = "admin.domain"
	
	list_display = ("domain", "tenant", "is_primary")
	search_fields = ("domain", "tenant__slug")
	list_filter = ("is_primary",)


if Tenant not in admin.site._registry:
	admin.site.register(Tenant, TenantAdmin)
if Domain not in admin.site._registry:
	admin.site.register(Domain, DomainAdmin)