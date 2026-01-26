from urllib.parse import urlencode

from django.contrib.auth.views import redirect_to_login
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse

from .models import TenantRequest, TenantRequestStatus

try:
	from django_tenants.utils import schema_context
except Exception:  # pragma: no cover
	schema_context = None

try:
	from apps.onboarding.tasks import auto_provision_free_tenant
except Exception:  # pragma: no cover
	auto_provision_free_tenant = None


def signup_view(request):
	tenant = getattr(request, "tenant", None)
	if tenant and getattr(tenant, "schema_name", None) != "public":
		# Tenant host should not expose public onboarding.
		if request.user.is_authenticated:
			return redirect("crm_dashboard")
		return redirect_to_login("/crm/")
	if request.method == "POST":
		company_name = (request.POST.get("company_name") or "").strip()
		desired_slug = (request.POST.get("desired_slug") or "").strip().lower()
		contact_email = (request.POST.get("contact_email") or "").strip().lower()
		contact_first = (request.POST.get("contact_first_name") or "").strip()
		contact_last = (request.POST.get("contact_last_name") or "").strip()
		contact_name = (f"{contact_first} {contact_last}".strip() or (request.POST.get("contact_name") or "").strip())
		plan_code = (request.POST.get("plan") or request.GET.get("plan") or "free").strip().lower()

		# Backend required validation (browser validation can be bypassed).
		errors: list[str] = []
		if not company_name:
			errors.append("Company name is required.")
		if not desired_slug:
			errors.append("Desired slug is required.")
		else:
			import re

			if not re.fullmatch(r"[a-z0-9-]+", desired_slug):
				errors.append("Desired slug must be lowercase letters, numbers, and hyphens only.")
		if not contact_first:
			errors.append("First name is required.")
		if not contact_last:
			errors.append("Last name is required.")
		if not contact_email:
			errors.append("Contact email is required.")

		if errors:
			# Re-render with the user's inputs preserved.
			return render(
				request,
				"onboarding/signup.html",
				{
					"plan": plan_code,
					"values": {
						"company_name": company_name,
						"desired_slug": desired_slug,
						"contact_first_name": contact_first,
						"contact_last_name": contact_last,
						"contact_email": contact_email,
						"contact_phone": (request.POST.get("contact_phone") or "").strip(),
					},
				},
				status=400,
			)

		tr = TenantRequest.objects.create(
			company_name=company_name,
			desired_slug=desired_slug,
			contact_name=contact_name,
			contact_first_name=contact_first,
			contact_last_name=contact_last,
			contact_email=contact_email,
			admin_email=contact_email,
			contact_phone=request.POST.get("contact_phone", "").strip(),
			requested_plan_code=plan_code,
		)
		url = reverse("tenant_signup_done")

		if plan_code == "free":
			# Start in background after DB commit so the done page can poll immediately.
			if auto_provision_free_tenant is not None:
				transaction.on_commit(lambda: auto_provision_free_tenant.delay(tenant_request_uid=str(tr.uid)))

		return HttpResponseRedirect(f"{url}?{urlencode({'r': str(tr.uid)})}")
	
	plan_code = (request.GET.get("plan") or "free").strip().lower()
	return render(request, "onboarding/signup.html", {"plan": plan_code, "values": {}})


def signup_done_view(request):
	tenant = getattr(request, "tenant", None)
	if tenant and getattr(tenant, "schema_name", None) != "public":
		if request.user.is_authenticated:
			return redirect("crm_dashboard")
		return redirect_to_login("/crm/")
	req_uid = (request.GET.get("r") or "").strip()
	tr = None
	if req_uid:
		tr = TenantRequest.objects.filter(uid=req_uid).first()
		if not tr:
			raise Http404()

	# Back-compat: older query params
	slug = (request.GET.get("slug") or (tr.desired_slug if tr else "") or "").strip().lower()
	email = (request.GET.get("email") or (tr.admin_email if tr else "") or (tr.contact_email if tr else "") or "").strip().lower()
	return render(
		request,
		"onboarding/signup_done.html",
		{"slug": slug, "email": email, "request_uid": (str(tr.uid) if tr else ""), "status": (tr.status if tr else "")},
	)


def signup_status_view(request, uid):
	"""
	HTMX polled endpoint:
	- while waiting: returns a small status fragment
	- when provisioned: HX-Redirect to tenant set-password link or tenant login
	"""
	tenant = getattr(request, "tenant", None)
	if tenant and getattr(tenant, "schema_name", None) != "public":
		raise Http404()

	tr = TenantRequest.objects.filter(uid=uid).first()
	if not tr:
		raise Http404()

	# If provisioned and we have a set-password token, redirect straight to the password set page.
	if tr.status == TenantRequestStatus.PROVISIONED and tr.provisioned_domain:
		host = tr.provisioned_domain
		if host and ":" not in host:
			port = (request.get_port() or "").strip()
			if port and port not in {"80", "443"}:
				host = f"{host}:{port}"

		scheme = request.scheme or "http"
		if tr.reset_uidb64 and tr.reset_token:
			target = f"{scheme}://{host}/reset/{tr.reset_uidb64}/{tr.reset_token}/"
		else:
			target = f"{scheme}://{host}/login/"

		resp = HttpResponse("Redirecting…")
		resp["HX-Redirect"] = target
		return resp

	return render(request, "onboarding/_signup_status.html", {"tr": tr})