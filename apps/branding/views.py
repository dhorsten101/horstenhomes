from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import UpdateView

from apps.branding.forms import TenantBrandingForm
from apps.branding.forms_theme import TenantThemeForm
from apps.branding.models import TenantBranding, UserThemePreference
from apps.core.mixins import TenantSchemaRequiredMixin


class TenantBrandingUpdateView(TenantSchemaRequiredMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView):
	model = TenantBranding
	form_class = TenantBrandingForm
	template_name = "branding/branding_form.html"
	success_url = reverse_lazy("crm_dashboard")

	def test_func(self):
		# Only staff users can change branding for now
		return bool(self.request.user and self.request.user.is_authenticated and self.request.user.is_staff)

	def get_object(self, queryset=None):
		obj, _ = TenantBranding.objects.get_or_create(pk=1)
		return obj

	def form_valid(self, form):
		resp = super().form_valid(form)
		messages.success(self.request, "Branding updated.")
		return resp


@login_required
@require_POST
def tenant_theme_update_view(request: HttpRequest) -> HttpResponse:
	tenant = getattr(request, "tenant", None)
	if not tenant or getattr(tenant, "schema_name", None) == "public":
		return redirect("landing")
	if not request.user.is_staff:
		return redirect("crm_dashboard")

	obj, _ = TenantBranding.objects.get_or_create(pk=1)
	form = TenantThemeForm(request.POST)
	if not form.is_valid():
		messages.error(request, "Could not update theme. Please check the values.")
		return redirect(request.META.get("HTTP_REFERER") or "crm_dashboard")

	active_theme = form.cleaned_data["active_theme"]
	themes = obj.themes or {}
	themes[active_theme] = {
		"primary": form.cleaned_data["primary"],
		"secondary": form.cleaned_data["secondary"],
		"body_bg": form.cleaned_data["body_bg"],
		"body_color": form.cleaned_data["body_color"],
	}
	obj.themes = themes
	obj.active_theme = active_theme
	obj.save(update_fields=["themes", "active_theme", "updated_at"])
	messages.success(request, "Theme updated.")
	return redirect(request.META.get("HTTP_REFERER") or "crm_dashboard")


@login_required
@require_POST
def user_theme_select_view(request: HttpRequest) -> HttpResponse:
	"""
	Allow any tenant user to choose which theme slot to use.
	Does NOT change colors (those are controlled by tenant staff).
	"""
	tenant = getattr(request, "tenant", None)
	if not tenant or getattr(tenant, "schema_name", None) == "public":
		return redirect("landing")

	theme_key = (request.POST.get("theme_key") or "").strip()
	if theme_key not in ("theme1", "theme2", "theme3"):
		messages.error(request, "Invalid theme selection.")
		return redirect(request.META.get("HTTP_REFERER") or "crm_dashboard")

	pref, _ = UserThemePreference.objects.get_or_create(user=request.user)
	pref.theme_key = theme_key
	pref.save(update_fields=["theme_key", "updated_at"])
	messages.success(request, "Theme changed.")
	return redirect(request.META.get("HTTP_REFERER") or "crm_dashboard")

