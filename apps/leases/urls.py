from django.urls import path

from apps.leases import views

app_name = "leases"

urlpatterns = [
	path("", views.LeaseListView.as_view(), name="list"),
	path("new/", views.LeaseCreateView.as_view(), name="create"),
	path("unit/<int:unit_pk>/new/", views.LeaseCreateForUnitView.as_view(), name="create_for_unit"),
	path("<int:pk>/", views.LeaseDetailView.as_view(), name="detail"),
	path("<int:pk>/edit/", views.LeaseUpdateView.as_view(), name="update"),
	path("<int:pk>/delete/", views.LeaseDeleteView.as_view(), name="delete"),
]

