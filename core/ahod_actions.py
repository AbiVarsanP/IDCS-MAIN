from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import OD, STATUS
from .helpers import get_post

@require_POST
def ahod_action_od(request, id):
    od = get_object_or_404(OD, id=id)
    status = request.POST.get('sts')
    if status == STATUS[1][0]:  # 'Approved'
        od.Astatus = STATUS[1][0]
        od.Mstatus = STATUS[1][0]
    elif status == STATUS[2][0]:  # 'Rejected'
        od.Astatus = STATUS[2][0]
        od.Mstatus = STATUS[2][0]
    od.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))
