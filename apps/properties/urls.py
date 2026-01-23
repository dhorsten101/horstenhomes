from django.urls import path

from apps.properties import views

app_name = "properties"

urlpatterns = [
	# Properties
	path("", views.PropertyListView.as_view(), name="property_list"),
	path("new/", views.PropertyCreateView.as_view(), name="property_create"),
	path("<int:pk>/", views.PropertyDetailView.as_view(), name="property_detail"),
	path("<int:pk>/edit/", views.PropertyUpdateView.as_view(), name="property_update"),
	path("<int:pk>/delete/", views.PropertyDeleteView.as_view(), name="property_delete"),
	# Units
	path("units/", views.UnitListView.as_view(), name="unit_list"),
	path("units/new/", views.UnitCreateView.as_view(), name="unit_create"),
	path("<int:property_pk>/units/new/", views.UnitCreateForPropertyView.as_view(), name="unit_create_for_property"),
	path("units/<int:pk>/", views.UnitDetailView.as_view(), name="unit_detail"),
	path("units/<int:pk>/edit/", views.UnitUpdateView.as_view(), name="unit_update"),
	path("units/<int:pk>/delete/", views.UnitDeleteView.as_view(), name="unit_delete"),
]

