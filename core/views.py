from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification, Student

# Student notifications view
@login_required
def notifications_view(request):
    student = Student.objects.get(user=request.user)
    # Latest 5 unread notifications for popup/dropdown
    latest_unread = Notification.objects.filter(user=student, is_read=False)[:5]
    # All notifications for history
    all_notifications = Notification.objects.filter(user=student)
    # Mark all unread as read when viewing history
    if request.method == "POST":
        Notification.objects.filter(user=student, is_read=False).update(is_read=True)
    return render(request, "student/notification_history.html", {
        "latest_unread": latest_unread,
        "all_notifications": all_notifications,
    })
from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import *
from .helpers import *
from .constants import *
from django.contrib.messages import error, success, warning
from io import BytesIO
from django.core.files import File
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.dateparse import parse_datetime   # ✅ must be here
from .models import GATEPASS, Student
import qrcode


# Student Profile View
@login_required
def student_profile(request):
    context = set_config(request)
    return render(request, 'student/profile.html', context)


@login_required
def hod_bonafide_view(request):
    context = set_config(request)
    context['bonafide_forms'] = BONAFIDE.objects.none()
    if 'duser' in context:
        try:
            hod_staff = Staff.objects.get(user=context['duser'].user)
            forms = BONAFIDE.objects.filter(
                models.Q(user__mentor=hod_staff) |
                models.Q(user__advisor=hod_staff) |
                models.Q(user__hod=hod_staff)
            ).distinct()
            if forms.exists():
                context['bonafide_forms'] = forms
        except Staff.DoesNotExist:
            pass
    return render(request, "hod/bonafide_hod.html", context)
def dash(request):
    context = set_config(request)
    if 'duser' not in context:
        return redirect('login')
    if not request.user.is_staff:
        context['BF'] = BONAFIDE.objects.filter(user=context['duser'].id)
        return render(request, 'student/dash.html', context=context)
    elif context['duser'].position == 0:
        context['allratings'] = IndividualStaffRating.objects.all()
        hod = HOD.objects.get(user=context['duser'])
        staff_list = [i for i in hod.staffs.all()]
        ratings = map_feedback(staff_list)
        context['ratings'] = ratings
        temp = IndividualStaffRating.objects.all()
        rating_logs = []
        for i in temp:
            if i.staff.department == context['duser'].department:
                rating_logs.append(i)
        context['my_rating'] = ratings[context['duser'].name]
        context['rating_log'] = rating_logs[:len(ratings)]
        # Bonafide forms for which the logged-in HOD is mentor, advisor, or HOD
        try:
            hod_staff = Staff.objects.get(user=context['duser'].user)
            context['bonafides'] = BONAFIDE.objects.filter(
                models.Q(user__mentor=hod_staff) |
                models.Q(user__advisor=hod_staff) |
                models.Q(user__hod=hod_staff)
            ).distinct()
        except Staff.DoesNotExist:
            context['bonafides'] = BONAFIDE.objects.none()
        return render(request, "hod/dash.html", context)
    else:
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        one_day_ago = now - timedelta(days=1)
        staff = context['duser']
        context['recent_od'] = OD.objects.filter(
            models.Q(user__advisor=staff) | models.Q(user__mentor=staff) | models.Q(user__hod=staff),
            created__gte=one_day_ago
        ).order_by('-created')[:5]
        context['recent_leave'] = LEAVE.objects.filter(
            models.Q(user__advisor=staff) | models.Q(user__mentor=staff) | models.Q(user__hod=staff),
            created__gte=one_day_ago
        ).order_by('-created')[:5]
        context['recent_gatepass'] = GATEPASS.objects.filter(
            models.Q(user__advisor=staff) | models.Q(user__mentor=staff) | models.Q(user__hod=staff),
            created__gte=one_day_ago
        ).order_by('-created')[:5]
        context['recent_bonafide'] = BONAFIDE.objects.filter(
            models.Q(user__advisor=staff) | models.Q(user__mentor=staff) | models.Q(user__hod=staff),
            created__gte=one_day_ago
        ).order_by('-created')[:5]
        context['aods'] = [i for i in OD.objects.all() if i.user.advisor.id == context['duser'].id]
        context['mods'] = [i for i in OD.objects.all() if i.user.mentor.id == context['duser'].id]
        context['hods'] = [i for i in OD.objects.all() if i.user.hod.id == context['duser'].id]
        return render(request, "staff/dash.html", context)



def login_user(request):

    context = {}
    if request.POST:
        reg = request.POST.get('reg')
        pwd = request.POST.get('pass')
        error_msg = None
        try:
            user_obj = User.objects.get(username=reg)
            user = authenticate(request, username=reg, password=pwd)
            if user is not None:
                login(request, user)
                return redirect(settings.LOGIN_REDIRECT_URL)
            else:
                error_msg = "Wrong Password"
        except User.DoesNotExist:
            error_msg = "Wrong Register Number"
        context['error_msg'] = error_msg

    return render(request, 'auth/login.html', context)

@login_required
def logout_user(request):
    logout(request)
    return redirect('dash')

# HOD MODULE
@login_required


def od(request):
    context = set_config(request)
    if request.method == "POST":
        sub = get_post(request, 'sub')
        body = get_post(request, 'reason')
        start = get_post(request, 'start')
        end = get_post(request, 'end')
        proff = request.FILES.get('proof')

        # Convert browser datetime string → Python datetime
        start = parse_datetime(start)
        end = parse_datetime(end)

        obj = OD(user=context['duser'], sub=sub, body=body,
                 start=start, end=end, proof=proff)
        obj.save()

        return redirect("dash")

    return render(request, 'student/od.html', context=context)


@login_required
def leave(request):
    context = set_config(request)
    if request.POST:
        from django.utils import timezone
        from datetime import datetime
        sub = get_post(request, 'sub')
        body = get_post(request, 'reason')
        f_raw = get_post(request, "from")
        t_raw = get_post(request, 'to')
        proff = request.FILES.get('proof')
        # Parse datetime fields, fallback to now if missing
        try:
            f = datetime.strptime(f_raw, "%Y-%m-%dT%H:%M") if f_raw else timezone.now()
        except Exception:
            f = timezone.now()
        try:
            t = datetime.strptime(t_raw, "%Y-%m-%dT%H:%M") if t_raw else timezone.now()
        except Exception:
            t = timezone.now()
        obj = LEAVE(user=context['duser'], sub=sub,
                    body=body, start=f, end=t, proof=proff)
        obj.save()

        return redirect("dash")

    return render(request, 'student/leave.html', context=context)

@login_required
def gatepass(request):
    context = set_config(request)
    action = request.GET.get('action', 'apply')
    context['action'] = action
    if request.method == "POST":
        sub = get_post(request, 'sub')
        start = get_post(request, 'start')
        end = get_post(request, 'end')
        # Parse datetime
        start = parse_datetime(start)
        end = parse_datetime(end)
        obj = GATEPASS(user=context['duser'], sub=sub, start=start, end=end)
        obj.save()
        return redirect("gatepass")
    if action == 'status':
        # Show all gatepasses for this student
        context['gatepasses'] = GATEPASS.objects.filter(user=context['duser']).order_by('-id')
    return render(request, 'student/gatepass_base.html', context=context)

@login_required
def staff_od_view(request):
    context = set_config(request)

    context['aods'] = [i for i in OD.objects.all() if i.user.advisor.id ==
                       context['duser'].id]
    context['mods'] = [i for i in OD.objects.all() if i.user.mentor.id ==
                       context['duser'].id]

    return render(request, 'staff/ods.html', context)

@login_required
def staff_leave_view(request):
    context = set_config(request)

    context['aods'] = [i for i in LEAVE.objects.all(
    ) if i.user.advisor.id == context['duser'].id]
    context['mods'] = [i for i in LEAVE.objects.all(
    ) if i.user.mentor.id == context['duser'].id]

    return render(request, 'staff/leaves.html', context)

@login_required
def staff_gatepass_view(request):
    context = set_config(request)

    context['aods'] = [i for i in GATEPASS.objects.all(
    ) if i.user.advisor.id == context['duser'].id]
    context['mods'] = [i for i in GATEPASS.objects.all(
    ) if i.user.mentor.id == context['duser'].id]

    return render(request, 'staff/gatepasss.html', context)

@login_required
def hod_od_view(request):
    context = set_config(request)

    context['mods'] = [i for i in OD.objects.all() if i.user.mentor.id ==
                       context['duser'].id]
    context['hods'] = [i for i in OD.objects.all() if i.user.hod.id ==
                       context['duser'].id or i.user.mentor.id != context['duser'].id]
    print(context)
    return render(request, 'hod/ods.html', context)

@login_required
def hod_leave_view(request):
    context = set_config(request)

    context['mods'] = [i for i in LEAVE.objects.all(
    ) if i.user.mentor.id == context['duser'].id]
    context['hods'] = [i for i in LEAVE.objects.all() if i.user.hod.id ==
                       context['duser'].id or i.user.mentor.id != context['duser'].id]
    print(context)
    return render(request, 'hod/leaves.html', context)

@login_required
def hod_gatepass_view(request):
    context = set_config(request)

    context['mods'] = [i for i in GATEPASS.objects.all(
    ) if i.user.mentor.id == context['duser'].id]
    context['hods'] = [i for i in GATEPASS.objects.all() if i.user.hod.id ==
                       context['duser'].id or i.user.mentor.id != context['duser'].id]
    print(context)
    return render(request, 'hod/gatepasss.html', context)

@login_required

@login_required
def staff_action_od(request, id):

    if request.POST:
        od = OD.objects.get(id=id)
        print(od.user.mentor.user.username, request.user)

        if str(od.user.mentor.user.username) == str(request.user):
            od.Mstatus = get_post(request, 'sts')
            if od.Mstatus == STATUS[2][0]:
                od.Astatus = STATUS[2][0]
                od.Hstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                user=od.user,
                message=f"Your OD request was {od.Mstatus} by Mentor"
            )
            print(od.Mstatus)

        if str(od.user.advisor.user.username) == str(request.user):
            od.Astatus = get_post(request, 'sts')
            if od.Astatus == STATUS[2][0]:
                od.Hstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                user=od.user,
                message=f"Your OD request was {od.Astatus} by Advisor"
            )
        if str(od.user.hod.user.username) == str(request.user):
            action_status = get_post(request, 'sts')
            if action_status == STATUS[1][0]:  # 'Approved'
                od.Mstatus = STATUS[1][0]
                od.Astatus = STATUS[1][0]
                od.Hstatus = STATUS[1][0]
            elif action_status == STATUS[2][0]:  # 'Rejected'
                od.Mstatus = STATUS[2][0]
                od.Astatus = STATUS[2][0]
                od.Hstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                user=od.user,
                message=f"Your OD request was {action_status} by HOD"
            )
            od.save()
            print(od.Astatus)
            return redirect("hod_od_view")

        od.save()
        print("Changed")

    return redirect("staff_od_view")

@login_required
def staff_action_leave(request, id):

    if request.POST:
        od = LEAVE.objects.get(id=id)
        print(od.user.mentor.user.username, request.user)

        if str(od.user.mentor.user.username) == str(request.user):
            od.Mstatus = get_post(request, 'sts')
            if od.Mstatus == STATUS[2][0]:
                od.Astatus = STATUS[2][0]
                od.Hstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                user=od.user,
                message=f"Your Leave request was {od.Mstatus} by Mentor"
            )
            print(od.Mstatus)

        if str(od.user.advisor.user.username) == str(request.user):
            od.Astatus = get_post(request, 'sts')
            if od.Astatus == STATUS[2][0]:
                od.Hstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                user=od.user,
                message=f"Your Leave request was {od.Astatus} by Advisor"
            )
        if str(od.user.hod.user.username) == str(request.user):
            action_status = get_post(request, 'sts')
            if action_status == STATUS[1][0]:  # 'Approved'
                od.Mstatus = STATUS[1][0]
                od.Astatus = STATUS[1][0]
                od.Hstatus = STATUS[1][0]
            elif action_status == STATUS[2][0]:  # 'Rejected'
                od.Mstatus = STATUS[2][0]
                od.Astatus = STATUS[2][0]
                od.Hstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                user=od.user,
                message=f"Your Leave request was {action_status} by HOD"
            )
            od.save()
            print(od.Astatus)
            return redirect("hod_leave_view")

        od.save()
        print("Changed")

    return redirect("staff_leave_view")


@login_required
def staff_action_gatepass(request, id):

    if request.POST:
        od = GATEPASS.objects.get(id=id)
        print(od.user.mentor.user.username, request.user)

        if str(od.user.mentor.user.username) == str(request.user):
            od.Mstatus = get_post(request, 'sts')
            if od.Mstatus == STATUS[2][0]:
                od.Astatus = STATUS[2][0]
                od.Hstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                user=od.user,
                message=f"Your Gatepass request was {od.Mstatus} by Mentor"
            )
            print(od.Mstatus)

        if str(od.user.advisor.user.username) == str(request.user):
            od.Astatus = get_post(request, 'sts')
            if od.Astatus == STATUS[2][0]:
                od.Hstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                user=od.user,
                message=f"Your Gatepass request was {od.Astatus} by Advisor"
            )
        if str(od.user.hod.user.username) == str(request.user):
            action_status = get_post(request, 'sts')
            if action_status == STATUS[1][0]:  # 'Approved'
                od.Mstatus = STATUS[1][0]
                od.Astatus = STATUS[1][0]
                od.Hstatus = STATUS[1][0]
            elif action_status == STATUS[2][0]:  # 'Rejected'
                od.Mstatus = STATUS[2][0]
                od.Astatus = STATUS[2][0]
                od.Hstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                user=od.user,
                message=f"Your Gatepass request was {action_status} by HOD"
            )
            od.save()
            print(od.Astatus)
            return redirect("hod_gatepass_view")

        od.save()
        print("Changed")

    return redirect("staff_gatepass_view")


@login_required
def upload_proof_od(request, id):
    if request.POST:
        comp = request.FILES.get('comp')
        od = OD.objects.get(id=id)
        od.certificate = comp
        od.save()

    return redirect('dash')


@login_required
def upload_proof_leave(request, id):
    if request.POST:
        comp = request.FILES.get('comp')
        od = LEAVE.objects.get(id=id)
        od.certificate = comp
        od.save()

    return redirect('dash')


# Feedback

#hodFeedback View

def hod_feedback_view(request):
    context = set_config(request)
    context['hod'] = HOD.objects.get(user=context['duser'])
    if context['hod'].department == 0:
        context['class'] = SECTION[:2] 
        
    elif context['hod'].department == 1 or context['hod'].department ==3 :
        context['class'] = SECTION[2:]
    
    else :
        context['class'] = SECTION[2]
    
    context['year'] = YEAR 
    
    context['spf'] = SpotFeedback.objects.filter(user=context['duser'])
    
    return render(request,"hod/feedback.html",context)

@login_required
def hod_feedback_toggle(request,id):
    if request.POST:
        obj = HOD.objects.get(id=id)
        obj.get_feedback = not obj.get_feedback
        obj.save()
        
    return redirect('hod_feedback_view')

@login_required
def hod_spot_feedback_toggle(request,id):
    if request.POST:
        obj = SpotFeedback.objects.get(id=id)
        obj.is_open = not obj.is_open
        obj.save()
        
    return redirect('hod_feedback_view')


@login_required
def hod_spot_feedback(request):
    context = set_config(request)
    if request.POST:
        staff = get_post(request,'staff')                           
        year = get_post(request,'yr')                           
        cls = get_post(request,'cls')
        
        students = Student.objects.filter(year=year)
        obj = SpotFeedback(user=context['duser'],staff=Staff.objects.get(id=staff),year=year,section=cls)
        obj.save()
        for i in students:
            obj.students.add(i)
        obj.save()
        context['duser'].get_spot_feedback = True
        context['duser'].save()
        
        hod = HOD.objects.filter(user=context['duser'])[0]
        hod.spot_feedback.add(obj)
        hod.save()
        
        # QR
        
        qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
        obj.url = request.build_absolute_uri(obj.get_absolute_url())
        qr.add_data(obj.url)
        
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        qr_code_image = BytesIO()
        img.save(qr_code_image, format='PNG')
        
         
        obj.qr_code.save(f'fqr_code{obj.id}.png', File(qr_code_image))

        obj.save()
    
    return redirect('hod_feedback_view')


@login_required
def student_feedback(request):
    context = set_config(request)

    temp = list(i.id for i in context['duser'].teaching_staffs.all())
    context['s_rating'] = []
    context['cs_rating'] = []
    
    hod = HOD.objects.get(user=context['duser'].hod)

    # spot feedback
    spf = SpotFeedback.objects.filter(user=context['duser'].hod)
    context['spf_staff']=[]
    for i in spf:
        if context['duser'] in i.students.all():
            context['spf_staff'].append(Staff.objects.get(user=i.staff.user))

        if context['duser'] in i.completed_students.all():
            context['cs_rating'].append(Staff.objects.get(user=i.staff.user))  
            
    if not hod.get_feedback:
        context['duser'].feedback_for.clear()
        return render(request, 'student/feedback.html', context)

    if hod.get_feedback:
        rec_f = list(i.staff.id for i in context['duser'].feedback_for.all())

    for i in temp:
        if i not in rec_f:
            context['s_rating'].append(
                context['duser'].teaching_staffs.get(id=i))
        else:
            context['cs_rating'].append(
                context['duser'].teaching_staffs.get(id=i))
    
    return render(request, 'student/feedback.html', context)


@login_required
def student_feedback_form(request, id,typ):
    context = set_config(request)
    
    ques = RatingQuestions.objects.all()
    context['ques'] = ques
    context['c_staff'] = Staff.objects.get(id=id)

    if request.POST:
        inrating = IndividualStaffRating(
            staff=context['c_staff'], student=context['duser'])
        inrating.save()
        for i in ques:
            comt = get_post(request, f"comment{i.id}")
            star = get_post(request, f"star{i.id}")
            obj = StaffRating(
                staff=context['c_staff'], student=context['duser'], ques=i, points=star, comments=comt)
            obj.save()
            inrating.ratings.add(obj)
            
        if typ=='gen':
            context['duser'].feedback_for.add(inrating)
            
            
        elif typ=='spf':
            hod = HOD.objects.get(user=context['duser'].hod)
            spot_feedbacks = hod.spot_feedback.filter(staff=context['c_staff'])
            for i in spot_feedbacks:
                if len(i.students.filter(user=context['duser'].user)) > 0:
                    i.feebacks.add(inrating)
                    i.students.remove(context['duser'])
                    i.completed_students.add(context['duser'])
                    i.save()
        else:
            pass
        
        context['duser'].feedback_history.add(inrating)
        context['duser'].save()

        inrating.is_feedbacked = True
        inrating.save()

        context['c_staff'].my_feedbacks.add(inrating)
        context['c_staff'].save()
        return redirect('student_feedback')

    return render(request, "feedbackform.html", context=context)

# END HOD MODULE

# CSFW


# EDC

# Bonafide View
@login_required
def bonafide_view(request):
    context = set_config(request)
    if request.POST:
        sub = get_post(request, 'sub')
        date = get_post(request, 'date')
        proff = request.FILES.get('proof')
        # Compose body from all relevant fields
        body_parts = []
        def add_body(label, key):
            val = get_post(request, key)
            if val:
                body_parts.append(f"{label}: {val}")
        add_body('Father\'s Name', 'fathers_name')
        add_body('Branch', 'branch')
        add_body('Year', 'year')
        add_body('Community', 'community')
        add_body('Other Community', 'other_community')
        add_body('Scholar Type', 'scholar_type')
        add_body('College Bus', 'college_bus')
        add_body('Boarding Point', 'boarding_point')
        add_body('Bus Type', 'bus_type')
        add_body('Bus Fare', 'bus_fare')
        add_body('First Graduate', 'first_graduate')
        add_body('Gov/Management', 'gov_mgmt')
        # Add other_purpose if present and selected
        if get_post(request, 'purpose') == 'Other':
            add_body('Other Purpose', 'other_purpose')
        body = " | ".join(body_parts)
        obj = BONAFIDE(user=context['duser'], sub=sub, body=body, date=date, proof=proff)
        obj.save()
        return redirect("dash")
    return render(request, 'student/bonafide_form.html', context=context)

# Staff Bonafides View
@login_required
def staff_bonafides(request):
    context = set_config(request)
    # Show bonafide requests for students who are mentees of the logged-in staff user
    staff = Staff.objects.get(user=request.user)
    # Bonafide forms for which the logged-in staff is the mentor
    context['mentee_bonafides'] = BONAFIDE.objects.filter(user__mentor=staff)
    # Bonafide forms for which the logged-in staff is the advisor (class forms)
    context['class_bonafides'] = BONAFIDE.objects.filter(user__advisor=staff)
    return render(request, 'staff/bonafides.html', context)

@login_required
def staff_action_bonafide(request, id):
    if request.POST:
        bonafide = BONAFIDE.objects.get(id=id)
        # Mentor action
        if str(bonafide.user.mentor.user.username) == str(request.user):
            bonafide.Mstatus = get_post(request, 'sts')
            if bonafide.Mstatus == STATUS[2][0]:
                bonafide.Astatus = STATUS[2][0]
                bonafide.Hstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                user=bonafide.user,
                message=f"Your Bonafide request was {bonafide.Mstatus} by Mentor"
            )
            bonafide.save()
        # Advisor action
        if str(bonafide.user.advisor.user.username) == str(request.user):
            bonafide.Astatus = get_post(request, 'sts')
            if bonafide.Astatus == STATUS[2][0]:
                bonafide.Hstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                user=bonafide.user,
                message=f"Your Bonafide request was {bonafide.Astatus} by Advisor"
            )
            bonafide.save()
        # HOD action
        if str(bonafide.user.hod.user.username) == str(request.user):
            action_status = get_post(request, 'sts')
            if action_status == STATUS[2][0]:  # 'Rejected'
                bonafide.Hstatus = STATUS[2][0]
            else:
                bonafide.Hstatus = STATUS[1][0]  # 'Approved'
            bonafide.Astatus = STATUS[1][0]  # Always set Advisor to 'Approved' for HOD action
            from .models import Notification
            Notification.objects.create(
                user=bonafide.user,
                message=f"Your Bonafide request was {action_status} by HOD"
            )
            bonafide.save()
            return redirect("hod_bonafide_view")
        return redirect("staff_bonafides")

