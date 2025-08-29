from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import OD, STATUS
from .helpers import get_post

@require_POST
def ahod_action_od(request, id):
    od = get_object_or_404(OD, id=id)
    status = request.POST.get('sts')
    ahod_hod_reason = request.POST.get('ahod_hod_reason', '').strip()
    # Only allow AHOD to act if Mentor and Advisor have approved
    if od.Mstatus == STATUS[1][0] and od.Astatus == STATUS[1][0]:
        if status == 'Approved_AHOD_HOD':
            od.AHstatus = STATUS[1][0]  # Approved
            od.Hstatus = STATUS[1][0]   # Approved
            od.ahod_hod_action = status
            od.ahod_hod_reason = ahod_hod_reason
        elif status == 'Rejected_AHOD_HOD':
            od.AHstatus = STATUS[2][0]  # Rejected
            od.Hstatus = STATUS[2][0]   # Rejected
            od.ahod_hod_action = status
            od.ahod_hod_reason = ahod_hod_reason
        elif status == STATUS[1][0]:  # 'Approved'
            od.AHstatus = STATUS[1][0]
        elif status == STATUS[2][0]:  # 'Rejected'
            od.AHstatus = STATUS[2][0]
            od.Hstatus = STATUS[2][0]  # Rejected
            od.Mstatus = STATUS[2][0]  # Rejected
            od.Astatus = STATUS[2][0]  # Rejected
        else:
            od.AHstatus = status  # For 'Meet Me' or other custom status
        od.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))
