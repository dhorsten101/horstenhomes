from django.contrib import admin

from apps.contacts.models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
	list_display = ("display_name", "email", "phone", "updated_at")
	search_fields = ("display_name", "email", "phone", "external_id")
	list_filter = ("source",)
