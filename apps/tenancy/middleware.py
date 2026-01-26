from django.http import HttpResponseForbidden

from apps.tenancy.models import TenantStatus


class TenantStatusMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response
	
	def __call__(self, request):
		tenant = getattr(request, "tenant", None)
		if tenant and getattr(tenant, "status", None) == TenantStatus.SUSPENDED:
			return HttpResponseForbidden("Tenant is suspended.")
		return self.get_response(request)