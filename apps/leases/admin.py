from django.contrib import admin

from apps.leases.models import Lease


@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
	list_display = ("unit", "primary_tenant", "status", "start_date", "end_date", "updated_at")
	list_filter = ("status",)
	search_fields = ("unit__unit_number", "unit__property__name", "primary_tenant__display_name", "external_id")

from django.contrib import admin

# Register your models here.
