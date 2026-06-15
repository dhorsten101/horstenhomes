from django.contrib import admin

from apps.rental_agents.models import RentalAgent


@admin.register(RentalAgent)
class RentalAgentAdmin(admin.ModelAdmin):
	list_display = ("name", "reference", "is_active", "updated_at")
	list_filter = ("is_active",)
	search_fields = ("name", "contact__display_name", "contact__email", "contact__phone", "reference")
	autocomplete_fields = ("contact",)
