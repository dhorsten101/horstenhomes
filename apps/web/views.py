from django.http import Http404
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import render


def home_view(request):
	return render(request, "web/home.html")


def crm_dashboard_view(request):
	tenant = getattr(request, "tenant", None)
	if not tenant or getattr(tenant, "schema_name", None) == "public":
		raise Http404()
	if not request.user.is_authenticated:
		return redirect_to_login(request.get_full_path())
	return render(request, "web/crm_dashboard.html")
