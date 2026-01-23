from django.contrib import admin

from apps.properties.models import Property, Unit


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
	list_display = ("name", "portfolio", "property_type", "is_archived", "updated_at")
	list_filter = ("property_type", "is_archived")
	search_fields = ("name", "external_id")


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
	list_display = ("unit_number", "property", "status", "updated_at")
	list_filter = ("status", "property")
	search_fields = ("unit_number", "external_id", "property__name")

from django.contrib import admin

# Register your models here.
