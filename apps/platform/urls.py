from django.urls import path

from . import views

app_name = "platform"

urlpatterns = [
	path("", views.dashboard_view, name="dashboard"),
	path("tenant-requests/", views.tenant_request_list_view, name="tenant_request_list"),
	path(
		"tenant-requests/<int:pk>/approve-provision/",
		views.tenant_request_approve_provision_view,
		name="tenant_request_approve_provision",
	),
	path("tenant-requests/<int:pk>/reject/", views.tenant_request_reject_view, name="tenant_request_reject"),
	path("tenant-requests/<int:pk>/delete/", views.tenant_request_delete_view, name="tenant_request_delete"),
	path("tenants/", views.tenant_list_view, name="tenant_list"),
	path("tenants/<int:pk>/suspend/", views.tenant_suspend_view, name="tenant_suspend"),
	path("tenants/<int:pk>/activate/", views.tenant_activate_view, name="tenant_activate"),
	path("tenants/<int:pk>/delete/", views.tenant_delete_view, name="tenant_delete"),
	path("domains/", views.domain_list_view, name="domain_list"),
	path("domains/<int:pk>/delete/", views.domain_delete_view, name="domain_delete"),
	path("logs/", views.log_list_view, name="log_list"),
	path("audits/", views.audit_list_view, name="audit_list"),
	path("alerts/", views.alert_list_view, name="alert_list"),
	path("metrics/", views.metrics_view, name="metrics"),
	path("system-logs/", views.system_logs_view, name="system_logs"),
]

