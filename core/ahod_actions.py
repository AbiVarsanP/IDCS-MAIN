from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import OD, STATUS
from .helpers import get_post

@require_POST
def ahod_action_od(request, id):
    od = get_object_or_404(OD, id=id)
    status = request.POST.get('sts')
    # Only allow AHOD to act if Mentor and Advisor have approved
    if od.Mstatus == STATUS[1][0] and od.Astatus == STATUS[1][0]:
        if status == STATUS[1][0]:  # 'Approved'
            od.AHstatus = STATUS[1][0]
        elif status == STATUS[2][0]:  # 'Rejected'
            od.AHstatus = STATUS[2][0]
        else:
            od.AHstatus = status  # For 'Meet Me' or other custom status
        od.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))
