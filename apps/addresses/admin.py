from django.contrib import admin

from apps.addresses.models import Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
	list_display = ("line1", "city", "country", "updated_at")
	search_fields = ("line1", "line2", "city", "postal_code", "country")
from django.contrib import admin

# Register your models here.
