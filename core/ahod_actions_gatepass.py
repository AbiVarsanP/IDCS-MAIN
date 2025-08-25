from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import GATEPASS, STATUS
from .helpers import get_post

@require_POST
def ahod_action_gatepass(request, id):
    gatepass = get_object_or_404(GATEPASS, id=id)
    status = request.POST.get('sts')
    if status == STATUS[1][0]:  # 'Approved'
        gatepass.Astatus = STATUS[1][0]
        gatepass.Mstatus = STATUS[1][0]
    elif status == STATUS[2][0]:  # 'Rejected'
        gatepass.Astatus = STATUS[2][0]
        gatepass.Mstatus = STATUS[2][0]
    gatepass.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))
