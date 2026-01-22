from __future__ import annotations

from typing import Callable

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.audits.models import AuditStatus
from apps.audits.services import audit_log
from apps.onboarding.models import TenantRequest, TenantRequestStatus
from apps.tenancy.models import Domain, Tenant, TenantStatus
from apps.tenancy.services.onboarding import provision_tenant, suspend_tenant, activate_tenant


def _public_schema_required(view: Callable[..., HttpResponse]):
	"""
	Keep "platform admin" views public-schema only.
	Otherwise tenant admins could see control-plane screens on their tenant host.
	"""

	def _wrapped(request: HttpRequest, *args, **kwargs):
		tenant = getattr(request, "tenant", None)
		if not tenant or getattr(tenant, "schema_name", None) != "public":
			raise Http404()
		return view(request, *args, **kwargs)

	return _wrapped


@staff_member_required
@_public_schema_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
	ctx = {
		"tenant_request_count": TenantRequest.objects.count(),
		"tenant_count": Tenant.objects.count(),
		"domain_count": Domain.objects.count(),
		"pending_requests": TenantRequest.objects.filter(status=TenantRequestStatus.NEW).count(),
	}
	return render(request, "platform/dashboard.html", ctx)


@staff_member_required
@_public_schema_required
def tenant_request_list_view(request: HttpRequest) -> HttpResponse:
	qs = TenantRequest.objects.order_by("-created_at")
	return render(request, "platform/tenant_request_list.html", {"tenant_requests": qs})


@staff_member_required
@_public_schema_required
def tenant_request_approve_provision_view(request: HttpRequest, pk: int) -> HttpResponse:
	if request.method != "POST":
		return HttpResponse(status=405)

	tr = get_object_or_404(TenantRequest, pk=pk)

	if tr.status in (TenantRequestStatus.PROVISIONED, TenantRequestStatus.REJECTED):
		messages.warning(request, f"Skipping {tr.company_name} (status={tr.status})")
		return redirect("platform:tenant_request_list")

	slug = (tr.desired_slug or "").strip().lower()
	if not slug:
		messages.error(request, f"{tr.company_name}: missing desired_slug")
		audit_log(
			action="onboarding.approve_rejected_missing_slug",
			obj=tr,
			status=AuditStatus.FAILURE,
			message="Missing desired_slug",
		)
		return redirect("platform:tenant_request_list")

	# Domain pattern matches onboarding admin behavior
	from django.conf import settings

	default_base_domain = getattr(settings, "BASE_TENANT_DOMAIN", "horstenhomes.local")
	domain = f"{slug}.{default_base_domain}"
	admin_email = (tr.admin_email or tr.contact_email or "").strip().lower()

	try:
		tenant = Tenant.objects.create(
			name=tr.company_name,
			slug=slug,
			status=TenantStatus.PROVISIONING,
			schema_name=slug,
		)
		Domain.objects.get_or_create(domain=domain, tenant=tenant, defaults={"is_primary": True})

		audit_log(
			action="onboarding.tenant_created",
			obj=tenant,
			metadata={
				"domain": domain,
				"source": "platform_ui",
				"tenant_request_id": tr.id,
				"contact_email": tr.contact_email,
				"admin_email": admin_email,
			},
			tenant_schema="public",
			request_id=str(tr.id),
		)
	except Exception as e:
		audit_log(
			action="onboarding.tenant_create_failed",
			obj=tr,
			status=AuditStatus.FAILURE,
			message=str(e),
			metadata={"slug": slug, "source": "platform_ui"},
			tenant_schema="public",
			request_id=str(tr.id),
		)
		messages.error(request, f"{tr.company_name}: tenant create failed: {e}")
		return redirect("platform:tenant_request_list")

	try:
		audit_log(
			action="onboarding.provision_started",
			obj=tenant,
			metadata={"domain": domain, "tenant_request_id": tr.id, "admin_email": admin_email},
			tenant_schema="public",
			request_id=str(tr.id),
		)

		reset_payload = provision_tenant(tenant=tenant, admin_email=admin_email)

		tenant.status = TenantStatus.ACTIVE
		tenant.save(update_fields=["status"])

		tr.status = TenantRequestStatus.PROVISIONED
		tr.converted_tenant_schema = tenant.schema_name
		tr.updated_at = timezone.now()
		tr.save(update_fields=["status", "converted_tenant_schema", "updated_at"])

		audit_log(
			action="onboarding.provision_completed",
			obj=tenant,
			metadata={"domain": domain, "tenant_request_id": tr.id},
			tenant_schema="public",
			request_id=str(tr.id),
		)

		messages.success(request, f"Provisioned {tr.company_name}: {domain}")

		if reset_payload:
			# Show a clickable set-password link (dev/testing convenience)
			host = request.get_host()  # e.g. admin.horstenhomes.local:8000
			port = host.split(":", 1)[1] if ":" in host else ""
			tenant_host = f"{domain}:{port}" if port else domain
			link = f"http://{tenant_host}/reset/{reset_payload['uidb64']}/{reset_payload['token']}/"
			messages.warning(request, f"Set-password link for {admin_email}: {link}")

	except Exception as e:
		tenant.status = TenantStatus.FAILED
		tenant.save(update_fields=["status"])

		audit_log(
			action="onboarding.provision_failed",
			obj=tenant,
			status=AuditStatus.FAILURE,
			message=str(e),
			metadata={"domain": domain, "tenant_request_id": tr.id},
			tenant_schema="public",
			request_id=str(tr.id),
		)

		messages.error(request, f"FAILED provisioning {tr.company_name}: {e}")

	return redirect("platform:tenant_request_list")


@staff_member_required
@_public_schema_required
def tenant_request_reject_view(request: HttpRequest, pk: int) -> HttpResponse:
	if request.method != "POST":
		return HttpResponse(status=405)

	tr = get_object_or_404(TenantRequest, pk=pk)
	if tr.status == TenantRequestStatus.PROVISIONED:
		messages.warning(request, f"Cannot reject {tr.company_name} (already provisioned).")
		return redirect("platform:tenant_request_list")

	tr.status = TenantRequestStatus.REJECTED
	tr.updated_at = timezone.now()
	tr.save(update_fields=["status", "updated_at"])
	audit_log(action="onboarding.request_rejected", obj=tr, metadata={"source": "platform_ui"})
	messages.success(request, f"Rejected request: {tr.company_name}")
	return redirect("platform:tenant_request_list")


@staff_member_required
@_public_schema_required
def tenant_request_delete_view(request: HttpRequest, pk: int) -> HttpResponse:
	if request.method != "POST":
		return HttpResponse(status=405)

	tr = get_object_or_404(TenantRequest, pk=pk)
	company = tr.company_name
	tr.delete()
	audit_log(action="onboarding.request_deleted", obj=None, metadata={"company_name": company, "source": "platform_ui"})
	messages.success(request, f"Deleted request: {company}")
	return redirect("platform:tenant_request_list")


@staff_member_required
@_public_schema_required
def tenant_list_view(request: HttpRequest) -> HttpResponse:
	qs = Tenant.objects.order_by("-created_at")
	return render(request, "platform/tenant_list.html", {"tenants": qs})


@staff_member_required
@_public_schema_required
def tenant_suspend_view(request: HttpRequest, pk: int) -> HttpResponse:
	if request.method != "POST":
		return HttpResponse(status=405)

	tenant = get_object_or_404(Tenant, pk=pk)
	if tenant.schema_name == "public":
		messages.error(request, "Refusing to suspend the public tenant.")
		return redirect("platform:tenant_list")

	suspend_tenant(tenant=tenant)
	audit_log(action="tenant.suspended", obj=tenant, metadata={"source": "platform_ui"})
	messages.success(request, f"Suspended tenant: {tenant.slug}")
	return redirect("platform:tenant_list")


@staff_member_required
@_public_schema_required
def tenant_activate_view(request: HttpRequest, pk: int) -> HttpResponse:
	if request.method != "POST":
		return HttpResponse(status=405)

	tenant = get_object_or_404(Tenant, pk=pk)
	if tenant.schema_name == "public":
		messages.error(request, "Refusing to activate the public tenant (already active).")
		return redirect("platform:tenant_list")

	activate_tenant(tenant=tenant)
	audit_log(action="tenant.activated", obj=tenant, metadata={"source": "platform_ui"})
	messages.success(request, f"Activated tenant: {tenant.slug}")
	return redirect("platform:tenant_list")


@staff_member_required
@_public_schema_required
def tenant_delete_view(request: HttpRequest, pk: int) -> HttpResponse:
	if request.method != "POST":
		return HttpResponse(status=405)

	tenant = get_object_or_404(Tenant, pk=pk)
	if tenant.schema_name == "public":
		messages.error(request, "Refusing to delete the public tenant.")
		return redirect("platform:tenant_list")

	slug = tenant.slug
	schema = tenant.schema_name
	tenant.delete()
	audit_log(action="tenant.deleted", obj=None, metadata={"slug": slug, "schema": schema, "source": "platform_ui"})
	messages.success(request, f"Deleted tenant record: {slug} (schema '{schema}' was not dropped)")
	return redirect("platform:tenant_list")


@staff_member_required
@_public_schema_required
def domain_list_view(request: HttpRequest) -> HttpResponse:
	qs = Domain.objects.select_related("tenant").order_by("domain")
	return render(request, "platform/domain_list.html", {"domains": qs})


@staff_member_required
@_public_schema_required
def domain_delete_view(request: HttpRequest, pk: int) -> HttpResponse:
	if request.method != "POST":
		return HttpResponse(status=405)

	domain = get_object_or_404(Domain.objects.select_related("tenant"), pk=pk)
	d = domain.domain
	tenant_slug = domain.tenant.slug if domain.tenant_id else None
	domain.delete()
	audit_log(action="domain.deleted", obj=None, metadata={"domain": d, "tenant": tenant_slug, "source": "platform_ui"})
	messages.success(request, f"Deleted domain: {d}")
	return redirect("platform:domain_list")

