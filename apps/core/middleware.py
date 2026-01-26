from __future__ import annotations

from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse


class AdminPortalGuardMiddleware:
	"""
	Block Django admin in tenant schemas and restrict public admin access.

	Goals:
	- Tenant admins (tenant schema users) should not access Django admin at all.
	- Public schema `/admin/` should be superuser-only (not just is_staff).
	"""

	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		path = getattr(request, "path", "") or ""
		if path.startswith("/admin/"):
			tenant = getattr(request, "tenant", None)

			# Never expose admin on tenant hosts/schemas.
			if tenant and getattr(tenant, "schema_name", None) != "public":
				raise Http404()

			# On public schema, allow unauthenticated users to hit the admin login page.
			user = getattr(request, "user", None)
			if getattr(user, "is_authenticated", False):
				# Superuser-only access on public schema
				if not getattr(user, "is_superuser", False):
					# If they can use Platform, send them there; otherwise forbid.
					if getattr(user, "is_staff", False):
						try:
							return redirect(reverse("platform:dashboard"))
						except NoReverseMatch:
							return redirect("/")
					return HttpResponseForbidden("Admin access restricted.")

		return self.get_response(request)

