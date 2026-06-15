from django.contrib import admin

from apps.marketing.models import PublicListing, PublicListingPhoto


class PublicListingPhotoInline(admin.TabularInline):
	model = PublicListingPhoto
	extra = 1
	fields = ("image", "caption", "sort_order", "is_primary")


@admin.register(PublicListing)
class PublicListingAdmin(admin.ModelAdmin):
	list_display = (
		"title",
		"property_name",
		"unit_number",
		"is_published",
		"rent_amount",
		"updated_at",
	)
	list_filter = ("is_published", "furnished")
	search_fields = ("title", "property_name", "summary", "unit_number", "address_city")
	readonly_fields = ("uid", "created_at", "updated_at")
	inlines = [PublicListingPhotoInline]
	fieldsets = (
		(None, {"fields": ("title", "summary", "is_published")}),
		(
			"Location",
			{"fields": ("property_name", "address_line1", "address_city", "unit_number")},
		),
		(
			"Unit details",
			{"fields": ("bedrooms", "bathrooms", "size_m2")},
		),
		(
			"Rent & lease",
			{
				"fields": (
					"rent_amount",
					"deposit_amount",
					"available_from",
					"lease_term_months",
					"furnished",
					"parking_spaces",
					"utilities_included",
					"pet_policy",
				)
			},
		),
		("Contact", {"fields": ("contact_email", "contact_phone")}),
		("Extras", {"fields": ("amenities",)}),
		("Meta", {"fields": ("uid", "created_at", "updated_at"), "classes": ("collapse",)}),
	)


@admin.register(PublicListingPhoto)
class PublicListingPhotoAdmin(admin.ModelAdmin):
	list_display = ("listing", "caption", "is_primary", "sort_order", "updated_at")
	list_filter = ("is_primary",)
	search_fields = ("listing__title", "caption")
