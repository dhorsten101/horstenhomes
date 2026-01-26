from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect, render

from apps.entitlements.models import Plan


def _public_only_or_redirect(request):
	tenant = getattr(request, "tenant", None)
	if tenant and getattr(tenant, "schema_name", None) != "public":
		if request.user.is_authenticated:
			return redirect("crm_dashboard")
		return redirect_to_login("/crm/")
	return None


def landing_view(request):
	resp = _public_only_or_redirect(request)
	if resp is not None:
		return resp
	return render(request, "marketing/landing.html")

def pricing_view(request):
	resp = _public_only_or_redirect(request)
	if resp is not None:
		return resp
	plans = Plan.objects.filter(is_active=True).order_by("unit_price", "code")
	return render(request, "marketing/pricing.html", {"plans": plans})


def pricing_component_view(request):
	resp = _public_only_or_redirect(request)
	if resp is not None:
		return resp
	plans = Plan.objects.filter(is_active=True).order_by("unit_price", "code")
	return render(request, "marketing/_pricing_component.html", {"plans": plans})