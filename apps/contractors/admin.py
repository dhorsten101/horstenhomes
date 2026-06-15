from django.contrib import admin

from apps.contractors.models import Contractor


@admin.register(Contractor)
class ContractorAdmin(admin.ModelAdmin):
	list_display = ("name", "trade", "email", "phone", "reference", "is_active", "updated_at")
	list_filter = ("is_active", "trade")
	search_fields = ("name", "trade", "email", "phone", "reference", "contacts__display_name")
	filter_horizontal = ("contacts",)
