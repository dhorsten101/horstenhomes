from django.contrib import admin

from apps.entitlements.models import FeatureFlag, Plan, QuotaUsage, TenantPlan


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
	list_display = ("code", "name", "is_active", "currency", "unit_price", "included_units", "updated_at")
	list_filter = ("is_active", "currency")
	search_fields = ("code", "name")


@admin.register(TenantPlan)
class TenantPlanAdmin(admin.ModelAdmin):
	list_display = ("tenant", "plan", "status", "starts_at", "ends_at", "updated_at")
	list_filter = ("status", "plan")
	search_fields = ("tenant__slug", "tenant__name", "plan__code")


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
	list_display = ("key", "default_enabled", "updated_at")
	list_filter = ("default_enabled",)
	search_fields = ("key", "description")


@admin.register(QuotaUsage)
class QuotaUsageAdmin(admin.ModelAdmin):
	list_display = ("tenant", "key", "period", "period_start", "value", "updated_at")
	list_filter = ("period", "key")
	search_fields = ("tenant__slug", "key")
