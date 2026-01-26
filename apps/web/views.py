from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import get_object_or_404, redirect, render

from apps.addresses.forms import AddressForm
from apps.addresses.models import Address
from apps.contacts.forms import ContactForm
from apps.contacts.models import Contact
from apps.leases.forms import LeaseForm
from apps.leases.models import Lease
from apps.portfolio.forms import PortfolioForm
from apps.portfolio.models import Portfolio
from apps.properties.forms import PropertyForm, UnitForm
from apps.properties.models import Property, Unit


def home_view(request):
	tenant = getattr(request, "tenant", None)
	if tenant and getattr(tenant, "schema_name", None) != "public":
		# Tenant host: the "home page" should be CRM (or login), not public marketing.
		if request.user.is_authenticated:
			return redirect("crm_dashboard")
		return redirect_to_login("/crm/")
	return render(request, "web/home.html")


def crm_dashboard_view(request):
	tenant = getattr(request, "tenant", None)
	if not tenant or getattr(tenant, "schema_name", None) == "public":
		# Public website (www/admin host). CRM is tenant-only.
		messages.info(request, "CRM is available on your tenant domain (e.g. company.horstenhomes.local).")
		# Prefer marketing landing if present; otherwise fall back to web home.
		try:
			return redirect("landing")
		except Exception:
			return redirect("home")
	if not request.user.is_authenticated:
		return redirect_to_login(request.get_full_path())

	ctx = {
		"totals": {
			"portfolios": Portfolio.objects.count(),
			"properties": Property.objects.count(),
			"units": Unit.objects.count(),
			"leases": Lease.objects.count(),
			"contacts": Contact.objects.count(),
			"addresses": Address.objects.count(),
		}
	}
	return render(request, "web/crm_dashboard.html", ctx)


WIZARD_SESSION_KEY = "crm_wizard"


def _tenant_login_required(request):
	tenant = getattr(request, "tenant", None)
	if not tenant or getattr(tenant, "schema_name", None) == "public":
		try:
			return redirect("landing")
		except Exception:
			return redirect("home")
	if not request.user.is_authenticated:
		return redirect_to_login(request.get_full_path())
	return None


def crm_wizard_start_view(request):
	"""
	Start fresh: Address -> Contact -> Portfolio -> Property -> Unit -> Lease.
	"""
	resp = _tenant_login_required(request)
	if resp is not None:
		return resp
	request.session[WIZARD_SESSION_KEY] = {}
	request.session.modified = True
	return redirect("crm_wizard_address")


def _wiz() -> dict:
	return {}


def _get_wiz(request) -> dict:
	return dict(request.session.get(WIZARD_SESSION_KEY) or {})


def _set_wiz(request, data: dict):
	request.session[WIZARD_SESSION_KEY] = data
	request.session.modified = True


def crm_wizard_address_view(request):
	resp = _tenant_login_required(request)
	if resp is not None:
		return resp
	wiz = _get_wiz(request)
	if request.method == "POST":
		form = AddressForm(request.POST)
		if form.is_valid():
			obj = form.save()
			wiz["address_id"] = obj.pk
			_set_wiz(request, wiz)
			messages.success(request, "Address created.")
			return redirect("crm_wizard_contact")
	else:
		form = AddressForm()
	return render(
		request,
		"web/crm_wizard_step.html",
		{"step": "address", "title": "Step 1 — Create address", "form": form, "back_url": "crm_dashboard"},
	)


def crm_wizard_contact_view(request):
	resp = _tenant_login_required(request)
	if resp is not None:
		return resp
	wiz = _get_wiz(request)
	if request.method == "POST":
		form = ContactForm(request.POST)
		if form.is_valid():
			obj = form.save()
			wiz["contact_id"] = obj.pk
			_set_wiz(request, wiz)
			messages.success(request, "Contact created.")
			return redirect("crm_wizard_portfolio")
	else:
		initial = {}
		if wiz.get("address_id"):
			initial["address"] = wiz["address_id"]
		form = ContactForm(initial=initial)
	return render(
		request,
		"web/crm_wizard_step.html",
		{"step": "contact", "title": "Step 2 — Create contact", "form": form, "back_url": "crm_wizard_address"},
	)


def crm_wizard_portfolio_view(request):
	resp = _tenant_login_required(request)
	if resp is not None:
		return resp
	wiz = _get_wiz(request)
	if request.method == "POST":
		form = PortfolioForm(request.POST)
		if form.is_valid():
			obj = form.save()
			wiz["portfolio_id"] = obj.pk
			_set_wiz(request, wiz)
			messages.success(request, "Portfolio created.")
			return redirect("crm_wizard_property")
	else:
		initial = {}
		if wiz.get("contact_id"):
			initial["owner_contact"] = wiz["contact_id"]
		form = PortfolioForm(initial=initial)
	return render(
		request,
		"web/crm_wizard_step.html",
		{"step": "portfolio", "title": "Step 3 — Create portfolio", "form": form, "back_url": "crm_wizard_contact"},
	)


def crm_wizard_property_view(request):
	resp = _tenant_login_required(request)
	if resp is not None:
		return resp
	wiz = _get_wiz(request)
	if request.method == "POST":
		form = PropertyForm(request.POST)
		if form.is_valid():
			obj = form.save()
			wiz["property_id"] = obj.pk
			_set_wiz(request, wiz)
			messages.success(request, "Property created.")
			return redirect("crm_wizard_unit")
	else:
		initial = {}
		if wiz.get("portfolio_id"):
			initial["portfolio"] = wiz["portfolio_id"]
		if wiz.get("address_id"):
			initial["address"] = wiz["address_id"]
		form = PropertyForm(initial=initial)
	return render(
		request,
		"web/crm_wizard_step.html",
		{"step": "property", "title": "Step 4 — Create property", "form": form, "back_url": "crm_wizard_portfolio"},
	)


def crm_wizard_unit_view(request):
	resp = _tenant_login_required(request)
	if resp is not None:
		return resp
	wiz = _get_wiz(request)
	if request.method == "POST":
		form = UnitForm(request.POST, request=request)
		if form.is_valid():
			obj = form.save()
			wiz["unit_id"] = obj.pk
			_set_wiz(request, wiz)
			messages.success(request, "Unit created.")
			return redirect("crm_wizard_lease")
	else:
		initial = {}
		if wiz.get("property_id"):
			initial["property"] = wiz["property_id"]
		form = UnitForm(initial=initial, request=request)
	return render(
		request,
		"web/crm_wizard_step.html",
		{"step": "unit", "title": "Step 5 — Create unit", "form": form, "back_url": "crm_wizard_property"},
	)


def crm_wizard_lease_view(request):
	resp = _tenant_login_required(request)
	if resp is not None:
		return resp
	wiz = _get_wiz(request)
	if request.method == "POST":
		form = LeaseForm(request.POST)
		if form.is_valid():
			obj = form.save()
			wiz["lease_id"] = obj.pk
			_set_wiz(request, wiz)
			messages.success(request, "Lease created.")
			return redirect("crm_wizard_done")
	else:
		initial = {}
		if wiz.get("unit_id"):
			initial["unit"] = wiz["unit_id"]
		if wiz.get("contact_id"):
			initial["primary_tenant"] = wiz["contact_id"]
		form = LeaseForm(initial=initial)
	return render(
		request,
		"web/crm_wizard_step.html",
		{"step": "lease", "title": "Step 6 — Create lease", "form": form, "back_url": "crm_wizard_unit"},
	)


def crm_wizard_done_view(request):
	resp = _tenant_login_required(request)
	if resp is not None:
		return resp
	wiz = _get_wiz(request)
	ctx = {"wiz": wiz}
	if wiz.get("address_id"):
		ctx["address"] = get_object_or_404(Address, pk=wiz["address_id"])
	if wiz.get("contact_id"):
		ctx["contact"] = get_object_or_404(Contact, pk=wiz["contact_id"])
	if wiz.get("portfolio_id"):
		ctx["portfolio"] = get_object_or_404(Portfolio, pk=wiz["portfolio_id"])
	if wiz.get("property_id"):
		ctx["property"] = get_object_or_404(Property, pk=wiz["property_id"])
	if wiz.get("unit_id"):
		ctx["unit"] = get_object_or_404(Unit, pk=wiz["unit_id"])
	if wiz.get("lease_id"):
		ctx["lease"] = get_object_or_404(Lease, pk=wiz["lease_id"])
	return render(request, "web/crm_wizard_done.html", ctx)
