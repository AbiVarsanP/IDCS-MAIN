from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import LEAVE, STATUS
from .helpers import get_post

@require_POST
def ahod_action_leave(request, id):
    leave = get_object_or_404(LEAVE, id=id)
    status = request.POST.get('sts')
    if status == STATUS[1][0]:  # 'Approved'
        leave.Astatus = STATUS[1][0]
        leave.Mstatus = STATUS[1][0]
    elif status == STATUS[2][0]:  # 'Rejected'
        leave.Astatus = STATUS[2][0]
        leave.Mstatus = STATUS[2][0]
    leave.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))
