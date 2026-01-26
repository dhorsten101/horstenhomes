from django.contrib import admin

from apps.portfolio.models import Portfolio


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
	list_display = ("name", "is_archived", "updated_at")
	search_fields = ("name", "description")
	list_filter = ("is_archived",)
