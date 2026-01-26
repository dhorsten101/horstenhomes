from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.audits.models import AuditEvent, AuditStatus
from apps.audits.services import audit_log
from apps.entitlements.models import Plan, TenantPlan, TenantPlanStatus
from apps.logs.metrics import get_system_metrics
from apps.logs.models import LogEntry
from apps.onboarding.models import TenantRequest, TenantRequestStatus
from apps.tenancy.models import Domain, Tenant, TenantStatus
from apps.tenancy.services.onboarding import activate_tenant, provision_tenant, suspend_tenant

from . import services as platform_services

try:
	from django_tenants.utils import schema_context
except Exception:  # pragma: no cover
	schema_context = None

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


TESTABLE_APP_LABELS: tuple[str, ...] = (
	"apps.contacts",
	"apps.addresses",
	"apps.portfolio",
	"apps.properties",
	"apps.leases",
	"apps.accounts",
	"apps.tenancy",
	"apps.audits",
	"apps.logs",
	"apps.activity",
)


def _list_test_files(app_label: str) -> list[str]:
	"""
	Best-effort list of test modules for UI display.
	"""
	base = Path(getattr(settings, "BASE_DIR", Path(".")))
	return platform_services.list_test_files(app_label=app_label, base_dir=base)


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
def entitlements_dashboard_view(request: HttpRequest) -> HttpResponse:
	return render(request, "platform/entitlements_dashboard.html")


@staff_member_required
@_public_schema_required
def plan_list_view(request: HttpRequest) -> HttpResponse:
	plans = Plan.objects.order_by("code")
	return render(request, "platform/plan_list.html", {"plans": plans})


@staff_member_required
@_public_schema_required
def tenant_plan_list_view(request: HttpRequest) -> HttpResponse:
	tenants = Tenant.objects.exclude(schema_name="public").order_by("slug")
	plans = Plan.objects.filter(is_active=True).order_by("code")
	tps = {tp.tenant_id: tp for tp in TenantPlan.objects.select_related("plan", "tenant")}
	return render(request, "platform/tenant_plan_list.html", {"tenants": tenants, "plans": plans, "tps": tps})


@staff_member_required
@_public_schema_required
def tenant_plan_set_view(request: HttpRequest, tenant_id: int) -> HttpResponse:
	if request.method != "POST":
		return HttpResponse(status=405)

	tenant = get_object_or_404(Tenant, pk=tenant_id)
	plan_id = int(request.POST.get("plan_id") or 0)
	status = (request.POST.get("status") or TenantPlanStatus.ACTIVE).strip()
	quota_overrides_raw = (request.POST.get("quota_overrides") or "").strip()
	feature_overrides_raw = (request.POST.get("feature_overrides") or "").strip()

	plan = get_object_or_404(Plan, pk=plan_id)

	def parse_json(raw: str) -> dict:
		if not raw:
			return {}
		return json.loads(raw)

	try:
		quota_overrides = parse_json(quota_overrides_raw)
		feature_overrides = parse_json(feature_overrides_raw)
	except Exception as e:
		messages.error(request, f"Invalid JSON overrides: {e}")
		return redirect("platform:tenant_plan_list")

	tp, created = TenantPlan.objects.get_or_create(tenant=tenant, defaults={"plan": plan, "status": status})
	tp.plan = plan
	tp.status = status
	tp.quota_overrides = quota_overrides
	tp.feature_overrides = feature_overrides
	tp.save()

	audit_log(
		action="entitlements.tenant_plan_set",
		obj=tenant,
		metadata={
			"tenant": tenant.slug,
			"plan": plan.code,
			"status": status,
			"created": created,
		},
		tenant_schema="public",
	)
	messages.success(request, f"Updated plan for {tenant.slug} -> {plan.code}")
	return redirect("platform:tenant_plan_list")

@staff_member_required
@_public_schema_required
def tests_view(request: HttpRequest) -> HttpResponse:
	"""
	Dev-only: Run Django tests from the Platform UI.

	This is intentionally restricted because running tests can create/drop test DBs
	and is not appropriate for production environments.
	"""
	if not settings.DEBUG:
		raise Http404()

	selected_app = ""
	result = None

	apps_ctx = [
		{"label": lbl, "tests": _list_test_files(lbl)}
		for lbl in TESTABLE_APP_LABELS
	]

	if request.method == "POST":
		selected_app = (request.POST.get("app") or "").strip()
		if selected_app not in TESTABLE_APP_LABELS:
			return HttpResponse(status=400)

		try:
			tr = platform_services.run_django_tests(app_label=selected_app, timeout_s=600)
			result = {
				"app": tr.app,
				"ok": tr.ok,
				"returncode": tr.returncode,
				"duration_ms": tr.duration_ms,
				"output": tr.output,
			}

			audit_log(
				action="tests.run",
				obj=None,
				status=AuditStatus.SUCCESS if tr.ok else AuditStatus.FAILURE,
				message=f"Ran tests for {selected_app} (exit={tr.returncode})",
				metadata={
					"app": selected_app,
					"returncode": tr.returncode,
					"duration_ms": tr.duration_ms,
				},
				tenant_schema="public",
			)

			if tr.ok:
				messages.success(request, f"Tests passed: {selected_app}")
			else:
				messages.error(request, f"Tests failed: {selected_app} (exit {tr.returncode})")
		except subprocess.TimeoutExpired:
			result = {
				"app": selected_app,
				"ok": False,
				"returncode": -1,
				"duration_ms": 0,
				"output": "Timed out running tests.",
			}
			audit_log(
				action="tests.run",
				obj=None,
				status=AuditStatus.FAILURE,
				message=f"Timed out running tests for {selected_app}",
				metadata={"app": selected_app, "duration_ms": 0},
				tenant_schema="public",
			)
			messages.error(request, f"Timed out: {selected_app}")
		except Exception as e:
			result = {
				"app": selected_app,
				"ok": False,
				"returncode": -1,
				"duration_ms": 0,
				"output": f"{type(e).__name__}: {e}",
			}
			audit_log(
				action="tests.run",
				obj=None,
				status=AuditStatus.FAILURE,
				message=f"Error running tests for {selected_app}: {e}",
				metadata={"app": selected_app, "duration_ms": 0},
				tenant_schema="public",
			)
			messages.error(request, f"Error running tests: {selected_app}")

	return render(
		request,
		"platform/tests.html",
		{"apps": apps_ctx, "selected_app": selected_app, "result": result},
	)


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

		reset_payload = provision_tenant(
			tenant=tenant,
			admin_email=admin_email,
			admin_first_name=(getattr(tr, "contact_first_name", "") or ""),
			admin_last_name=(getattr(tr, "contact_last_name", "") or ""),
		)

		tenant.status = TenantStatus.ACTIVE
		tenant.save(update_fields=["status"])

		tr.status = TenantRequestStatus.PROVISIONED
		tr.converted_tenant_schema = tenant.schema_name
		tr.provisioned_domain = domain
		if reset_payload:
			tr.reset_uidb64 = reset_payload.get("uidb64", "") or ""
			tr.reset_token = reset_payload.get("token", "") or ""
		tr.updated_at = timezone.now()
		tr.save(update_fields=["status", "converted_tenant_schema", "provisioned_domain", "reset_uidb64", "reset_token", "updated_at"])

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
			login_link = f"http://{tenant_host}/login/"
			link = f"http://{tenant_host}/reset/{reset_payload['uidb64']}/{reset_payload['token']}/"
			messages.info(request, f"Tenant login: {login_link}")
			messages.warning(request, f"Set-password link for {admin_email}: {link}")
		else:
			# If the admin user already had a password, still show the correct login URL.
			host = request.get_host()
			port = host.split(":", 1)[1] if ":" in host else ""
			tenant_host = f"{domain}:{port}" if port else domain
			messages.info(request, f"Tenant login: http://{tenant_host}/login/")

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
def tenant_switch_view(request: HttpRequest) -> HttpResponse:
	"""
	Convenience page: quickly jump from public control-plane to tenant hosts.

	This does NOT bypass authentication — tenant users are tenant-local.
	It simply builds correct tenant URLs (including dev port) so you can switch fast.
	"""
	q = (request.GET.get("q") or "").strip().lower()

	tenants_qs = Tenant.objects.exclude(schema_name="public").order_by("slug")
	if q:
		tenants_qs = tenants_qs.filter(slug__icontains=q) | tenants_qs.filter(name__icontains=q)

	tenants = list(tenants_qs)
	tenant_ids = [t.id for t in tenants]
	primary_domains = {
		d.tenant_id: d.domain
		for d in Domain.objects.filter(tenant_id__in=tenant_ids, is_primary=True).only("tenant_id", "domain")
	}

	base_domain = getattr(settings, "BASE_TENANT_DOMAIN", "horstenhomes.local")
	rows = platform_services.build_tenant_switch_rows(
		tenants=tenants,
		primary_domains=primary_domains,
		request_host=request.get_host(),
		request_scheme=request.scheme,
		base_domain=base_domain,
	)

	return render(request, "platform/tenant_switch.html", {"rows": rows, "q": q})


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


@staff_member_required
@_public_schema_required
def log_list_view(request: HttpRequest) -> HttpResponse:
	"""
	View runtime logs. Default schema=public; optional schema=<tenant_schema>.
	"""
	schema = (request.GET.get("schema") or "public").strip()
	limit = min(int(request.GET.get("limit") or 200), 1000)
	level = (request.GET.get("level") or "").strip().upper()

	def fetch():
		qs = LogEntry.objects.all().order_by("-created_at")
		if level:
			qs = qs.filter(level=level)
		return qs[:limit]

	if schema != "public":
		if schema_context is None:
			raise Http404()
		with schema_context(schema):
			rows = list(fetch())
	else:
		rows = list(fetch())

	# Populate schema choices from public schema.
	schemas = ["public"]
	if schema_context is not None:
		with schema_context("public"):
			schemas += list(Tenant.objects.exclude(schema_name="public").values_list("schema_name", flat=True))

	return render(
		request,
		"platform/log_list.html",
		{"logs": rows, "schema": schema, "schemas": schemas, "limit": limit, "level": level},
	)


@staff_member_required
@_public_schema_required
def audit_list_view(request: HttpRequest) -> HttpResponse:
	"""
	View audit events. Default schema=public; optional schema=<tenant_schema>.
	"""
	schema = (request.GET.get("schema") or "public").strip()
	limit = min(int(request.GET.get("limit") or 200), 1000)
	status = (request.GET.get("status") or "").strip().lower()

	def fetch():
		qs = AuditEvent.objects.all().order_by("-created_at")
		if status in {"success", "failure"}:
			qs = qs.filter(status=status)
		return list(qs[:limit])

	if schema != "public":
		if schema_context is None:
			raise Http404()
		with schema_context(schema):
			rows = fetch()
	else:
		rows = fetch()

	schemas = ["public"]
	if schema_context is not None:
		with schema_context("public"):
			schemas += list(Tenant.objects.exclude(schema_name="public").values_list("schema_name", flat=True))

	return render(
		request,
		"platform/audit_list.html",
		{"audits": rows, "schema": schema, "schemas": schemas, "limit": limit, "status": status},
	)


@staff_member_required
@_public_schema_required
def alert_list_view(request: HttpRequest) -> HttpResponse:
	"""
	Alerts = high-severity runtime logs + failing audit events (simple, production-safe baseline).
	"""
	schema = (request.GET.get("schema") or "public").strip()
	limit = min(int(request.GET.get("limit") or 200), 1000)

	def fetch_logs():
		return list(
			LogEntry.objects.filter(level__in=["ERROR", "CRITICAL"]).order_by("-created_at")[:limit]
		)

	def fetch_audits():
		return list(
			AuditEvent.objects.filter(status=AuditStatus.FAILURE).order_by("-created_at")[:limit]
		)

	if schema != "public":
		if schema_context is None:
			raise Http404()
		with schema_context(schema):
			error_logs = fetch_logs()
			failed_audits = fetch_audits()
	else:
		error_logs = fetch_logs()
		failed_audits = fetch_audits()

	schemas = ["public"]
	if schema_context is not None:
		with schema_context("public"):
			schemas += list(Tenant.objects.exclude(schema_name="public").values_list("schema_name", flat=True))

	return render(
		request,
		"platform/alert_list.html",
		{"schema": schema, "schemas": schemas, "limit": limit, "error_logs": error_logs, "failed_audits": failed_audits},
	)


@staff_member_required
@_public_schema_required
def system_logs_view(request: HttpRequest) -> HttpResponse:
	"""
	Show raw docker logs for core services (dev-focused).
	Requires docker CLI in the web container + docker socket mounted.
	"""
	service = (request.GET.get("service") or "web").strip().lower()
	tail = min(int(request.GET.get("tail") or 300), 5000)

	containers = {
		"web": "hh-web",
		"postgres": "hh-postgres",
		"redis": "hh-redis",
	}
	name = containers.get(service, "hh-web")

	docker_path = shutil.which("docker")
	output = ""
	error = ""

	if not docker_path:
		error = "docker CLI not available in container (rebuild dev image with docker CLI)."
	else:
		try:
			res = subprocess.run(
				["docker", "logs", "--tail", str(tail), name],
				check=False,
				capture_output=True,
				text=True,
				timeout=5,
			)
			output = (res.stdout or "") + (res.stderr or "")
			if res.returncode != 0:
				error = f"docker logs exited {res.returncode}"
		except Exception as e:
			error = f"{type(e).__name__}: {e}"

	return render(
		request,
		"platform/system_logs.html",
		{"service": service, "tail": tail, "output": output, "error": error, "services": list(containers.keys())},
	)


@staff_member_required
@_public_schema_required
def metrics_view(request: HttpRequest) -> HttpResponse:
	m = get_system_metrics()
	return render(request, "platform/metrics.html", {"m": m})


@staff_member_required
@_public_schema_required
def db_view(request: HttpRequest) -> HttpResponse:
	"""
	Lightweight "DB insights" page powered by `pg_stat_statements`.

	Notes:
	- This is cluster-wide, not schema-per-tenant. We provide a best-effort
	  schema filter by matching SQL text (useful when queries include schema-qualified tables).
	"""
	limit = min(int(request.GET.get("limit") or 50), 200)
	schema_filter = (request.GET.get("schema_filter") or "").strip()
	error = ""

	try:
		top_total, top_mean, top_calls = platform_services.get_pg_stat_statements(limit=limit, schema_filter=schema_filter)
	except Exception as e:
		top_total = []
		top_mean = []
		top_calls = []
		error = f"{type(e).__name__}: {e}"

	# Populate schema choices from public schema (for filtering convenience).
	schemas: list[str] = []
	if schema_context is not None:
		with schema_context("public"):
			schemas = list(Tenant.objects.exclude(schema_name="public").values_list("schema_name", flat=True))

	return render(
		request,
		"platform/db.html",
		{
			"limit": limit,
			"schema_filter": schema_filter,
			"schemas": schemas,
			"error": error,
			"top_total": top_total,
			"top_mean": top_mean,
			"top_calls": top_calls,
		},
	)

