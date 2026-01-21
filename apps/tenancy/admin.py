from django.contrib import admin
from .models import Tenant, Domain


from django.contrib import admin, messages

from apps.tenancy.models import Tenant, Domain, TenantStatus
from apps.tenancy.services.onboarding import provision_tenant, suspend_tenant, activate_tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
	list_display = ("name", "slug", "schema_name", "status", "created_at")
	search_fields = ("name", "slug", "schema_name")
	list_filter = ("status",)
	actions = ("action_provision", "action_suspend", "action_activate")
	
	@admin.action(description="Provision selected tenants (create schema + migrate)")
	def action_provision(self, request, queryset):
		for t in queryset:
			try:
				provision_tenant(tenant=t)
				self.message_user(request, f"Provisioned: {t.slug}", level=messages.SUCCESS)
			except Exception as e:
				t.status = TenantStatus.FAILED
				t.save(update_fields=["status"])
				self.message_user(request, f"FAILED: {t.slug} → {e}", level=messages.ERROR)
	
	@admin.action(description="Suspend selected tenants")
	def action_suspend(self, request, queryset):
		for t in queryset:
			suspend_tenant(tenant=t)
		self.message_user(request, "Suspended selected tenants.", level=messages.SUCCESS)
	
	@admin.action(description="Activate selected tenants")
	def action_activate(self, request, queryset):
		for t in queryset:
			activate_tenant(tenant=t)
		self.message_user(request, "Activated selected tenants.", level=messages.SUCCESS)


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
	list_display = ("domain", "tenant", "is_primary")
	search_fields = ("domain", "tenant__slug")
	list_filter = ("is_primary",)