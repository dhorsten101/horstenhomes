from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import AuditEvent


@staff_member_required
def audit_list(request):
	qs = AuditEvent.objects.all()
	
	action = request.GET.get("action", "").strip()
	actor = request.GET.get("actor", "").strip()
	rid = request.GET.get("request_id", "").strip()
	
	if action:
		qs = qs.filter(action__icontains=action)
	if actor:
		qs = qs.filter(actor_email__icontains=actor)
	if rid:
		qs = qs.filter(request_id=rid)
	
	paginator = Paginator(qs, 50)
	page = paginator.get_page(request.GET.get("page"))
	
	return render(request, "audits/audits_list.html", {"page": page, "filters": {"action": action, "actor": actor, "request_id": rid}})


@staff_member_required
def audit_detail(request, pk: int):
	ev = get_object_or_404(AuditEvent, pk=pk)
	return render(request, "audits/audits_detail.html", {"ev": ev})