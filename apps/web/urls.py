from django.urls import path

from . import views

urlpatterns = [
	path("", views.home_view, name="home"),
	path("crm/", views.crm_dashboard_view, name="crm_dashboard"),
	path("crm/wizard/", views.crm_wizard_start_view, name="crm_wizard_start"),
	path("crm/wizard/address/", views.crm_wizard_address_view, name="crm_wizard_address"),
	path("crm/wizard/contact/", views.crm_wizard_contact_view, name="crm_wizard_contact"),
	path("crm/wizard/portfolio/", views.crm_wizard_portfolio_view, name="crm_wizard_portfolio"),
	path("crm/wizard/property/", views.crm_wizard_property_view, name="crm_wizard_property"),
	path("crm/wizard/unit/", views.crm_wizard_unit_view, name="crm_wizard_unit"),
	path("crm/wizard/lease/", views.crm_wizard_lease_view, name="crm_wizard_lease"),
	path("crm/wizard/done/", views.crm_wizard_done_view, name="crm_wizard_done"),
]