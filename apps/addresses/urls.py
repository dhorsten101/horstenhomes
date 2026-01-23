from django.urls import path

from apps.addresses import views

app_name = "addresses"

urlpatterns = [
	path("", views.AddressListView.as_view(), name="list"),
	path("new/", views.AddressCreateView.as_view(), name="create"),
	path("<int:pk>/", views.AddressDetailView.as_view(), name="detail"),
	path("<int:pk>/edit/", views.AddressUpdateView.as_view(), name="update"),
	path("<int:pk>/delete/", views.AddressDeleteView.as_view(), name="delete"),
]

