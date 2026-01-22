from __future__ import annotations

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from apps.audits.services import audit_log
from apps.audits.models import AuditStatus


@receiver(user_logged_in)
def audit_login(sender, request, user, **kwargs):
	audit_log(action="auth.login.success", obj=user, metadata={"backend": request.session.get("_auth_user_backend", "")})


@receiver(user_logged_out)
def audit_logout(sender, request, user, **kwargs):
	# user can be None on some flows
	audit_log(action="auth.logout", obj=user, metadata={})


@receiver(user_login_failed)
def audit_login_failed(sender, credentials, request, **kwargs):
	# Never store raw password
	email = (credentials or {}).get("username") or (credentials or {}).get("email") or ""
	audit_log(
		action="auth.login.failed",
		status=AuditStatus.FAILURE,
		message="Invalid credentials",
		metadata={"attempted_identity": email},
	)