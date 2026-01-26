from django.conf import settings
from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html

from apps.audits.admin_mixins import AdminAuditMixin
from apps.audits.models import AuditStatus
from apps.audits.services import audit_log
from apps.onboarding.models import TenantRequest, TenantRequestStatus
from apps.tenancy.models import Domain, Tenant, TenantStatus
from apps.tenancy.services.onboarding import provision_tenant

DEFAULT_BASE_DOMAIN = getattr(settings, "BASE_TENANT_DOMAIN", "horstenhomes.local")


@admin.register(TenantRequest)
class TenantRequestAdmin(AdminAuditMixin, admin.ModelAdmin):
	"""
	Public admin workflow:
	  1) TenantRequest created via /signup/ (public schema)
	  2) Staff reviews in admin
	  3) Action: Approve + Provision -> creates Tenant + Domain (public) and provisions schema
	"""
	
	audit_action_prefix = "admin.tenantrequest"
	
	list_display = ("company_name", "contact_email", "admin_email", "desired_slug", "status", "created_at")
	list_editable = ("admin_email",)
	list_filter = ("status",)
	search_fields = ("company_name", "contact_email", "admin_email", "desired_slug")
	ordering = ("-created_at",)
	actions = ("action_approve_and_provision",)
	
	@admin.action(description="Approve + Provision (create tenant + domain + migrate)")
	def action_approve_and_provision(self, request, queryset):
		for tr in queryset:
			# guardrails
			if tr.status in (TenantRequestStatus.PROVISIONED, TenantRequestStatus.REJECTED):
				self.message_user(
					request,
					f"Skipping {tr.company_name} (status={tr.status})",
					level=messages.WARNING,
				)
				continue
			
			slug = (tr.desired_slug or "").strip().lower()
			if not slug:
				self.message_user(request, f"{tr.company_name}: missing desired_slug", level=messages.ERROR)
				audit_log(
					action="onboarding.approve_rejected_missing_slug",
					obj=tr,
					status=AuditStatus.FAILURE,
					message="Missing desired_slug",
				)
				continue
			
			# Create tenant row (public schema). Schema creation may happen via auto_create_schema,
			# but we still treat this as "provisioning" until service finishes.
			try:
				tenant = Tenant.objects.create(
					name=tr.company_name,
					slug=slug,
					status=TenantStatus.PROVISIONING,
					schema_name=slug,  # explicit
				)
				
				# Ensure domain record (public schema)
				domain = f"{slug}.{DEFAULT_BASE_DOMAIN}"
				Domain.objects.get_or_create(
					domain=domain,
					tenant=tenant,
					defaults={"is_primary": True},
				)
				
				audit_log(
					action="onboarding.tenant_created",
					obj=tenant,
					metadata={
						"domain": domain,
						"source": "admin_action",
						"tenant_request_id": tr.id,
						"contact_email": tr.contact_email,
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
					metadata={"slug": slug, "source": "admin_action"},
					tenant_schema="public",
					request_id=str(tr.id),
				)
				self.message_user(request, f"{tr.company_name}: tenant create failed: {e}", level=messages.ERROR)
				continue
			
			# Provision schema + migrate + create tenant admin user (inside your service)
			try:
				admin_email = (tr.admin_email or tr.contact_email or "").strip().lower()

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
				if reset_payload:
					# Build a tenant-local set-password link (no email sending required).
					host = request.get_host()  # e.g. admin.horstenhomes.local:8000
					port = host.split(":", 1)[1] if ":" in host else ""
					tenant_host = f"{domain}:{port}" if port else domain
					link = f"http://{tenant_host}/reset/{reset_payload['uidb64']}/{reset_payload['token']}/"
					self.message_user(
						request,
						format_html("Set-password link for {}: <a href='{}'>{}</a>", admin_email, link, link),
						level=messages.WARNING,
					)
					tr.provisioned_domain = domain
					tr.reset_uidb64 = reset_payload.get("uidb64", "") or ""
					tr.reset_token = reset_payload.get("token", "") or ""
				
				tenant.status = TenantStatus.ACTIVE
				tenant.save(update_fields=["status"])
				
				tr.status = TenantRequestStatus.PROVISIONED
				tr.converted_tenant_schema = tenant.schema_name
				tr.updated_at = timezone.now()
				tr.save(update_fields=["status", "converted_tenant_schema", "provisioned_domain", "reset_uidb64", "reset_token", "updated_at"])
				
				audit_log(
					action="onboarding.provision_completed",
					obj=tenant,
					metadata={"domain": domain, "tenant_request_id": tr.id},
					tenant_schema="public",
					request_id=str(tr.id),
				)
				
				self.message_user(request, f"Provisioned {tr.company_name}: {domain}", level=messages.SUCCESS)
			
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
				
				self.message_user(request, f"FAILED provisioning {tr.company_name}: {e}", level=messages.ERROR)