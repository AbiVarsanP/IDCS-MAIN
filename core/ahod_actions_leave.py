from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import LEAVE, STATUS
from .helpers import get_post

@require_POST
def ahod_action_leave(request, id):
    leave = get_object_or_404(LEAVE, id=id)
    status = request.POST.get('sts')
    ahod_hod_reason = request.POST.get('ahod_hod_reason', '').strip()
    if status == 'Approved_AHOD_HOD':
        leave.AHstatus = STATUS[1][0]
        leave.Hstatus = STATUS[1][0]
        leave.ahod_hod_action = status
        leave.ahod_hod_reason = ahod_hod_reason
    elif status == 'Rejected_AHOD_HOD':
        leave.AHstatus = STATUS[2][0]
        leave.Hstatus = STATUS[2][0]
        leave.ahod_hod_action = status
        leave.ahod_hod_reason = ahod_hod_reason
    elif status == STATUS[1][0]:  # 'Approved'
        leave.AHstatus = STATUS[1][0]
    elif status == STATUS[2][0]:  # 'Rejected'
        leave.AHstatus = STATUS[2][0]
    else:
        leave.AHstatus = status  # For 'Meet Me' or other custom status
    leave.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))
