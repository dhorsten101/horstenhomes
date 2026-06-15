from django.contrib.auth.views import redirect_to_login
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django_tenants.utils import schema_context

from apps.marketing.models import PublicListing


def _public_only_or_redirect(request):
	tenant = getattr(request, "tenant", None)
	if tenant and getattr(tenant, "schema_name", None) != "public":
		if request.user.is_authenticated:
			return redirect("crm_dashboard")
		return redirect_to_login("/crm/")
	return None


def _published_public_listings(limit: int = 100) -> list[PublicListing]:
	with schema_context("public"):
		qs = (
			PublicListing.objects.filter(is_published=True)
			.prefetch_related("photos")
			.order_by("-updated_at")[:limit]
		)
		return list(qs)


def landing_view(request):
	tenant = getattr(request, "tenant", None)
	is_public_site = not tenant or getattr(tenant, "schema_name", None) == "public"

	rows = _published_public_listings()
	featured = rows[0] if rows else None

	ctx: dict = {
		"listing": featured,
		"listings": rows,
		"is_public_site": is_public_site,
	}
	if is_public_site:
		ctx["pricing_component_url"] = reverse("marketing:pricing_component")

	return render(request, "marketing/landing.html", ctx)


def listing_detail_view(request, pk: int):
	with schema_context("public"):
		listing = get_object_or_404(
			PublicListing.objects.filter(is_published=True).prefetch_related("photos"),
			pk=pk,
		)
	return render(request, "marketing/listing_detail.html", {"listing": listing})


def pricing_view(request):
	resp = _public_only_or_redirect(request)
	if resp is not None:
		return resp
	from apps.entitlements.models import Plan

	plans = Plan.objects.filter(is_active=True).order_by("unit_price", "code")
	return render(request, "marketing/pricing.html", {"plans": plans})


def pricing_component_view(request):
	resp = _public_only_or_redirect(request)
	if resp is not None:
		return resp
	from apps.entitlements.models import Plan

	plans = Plan.objects.filter(is_active=True).order_by("unit_price", "code")
	return render(request, "marketing/_pricing_component.html", {"plans": plans})
