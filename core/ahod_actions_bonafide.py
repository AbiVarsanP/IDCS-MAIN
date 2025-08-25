from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import BONAFIDE, STATUS
from .helpers import get_post

@require_POST
def ahod_action_bonafide(request, id):
    bonafide = get_object_or_404(BONAFIDE, id=id)
    status = request.POST.get('sts')
    if status == STATUS[1][0]:  # 'Approved'
        bonafide.Astatus = STATUS[1][0]
        bonafide.Mstatus = STATUS[1][0]
    elif status == STATUS[2][0]:  # 'Rejected'
        bonafide.Astatus = STATUS[2][0]
        bonafide.Mstatus = STATUS[2][0]
    bonafide.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))
