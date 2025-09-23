from django.contrib.auth import get_user_model

# View for HOD to see all staff in their department
from django.contrib.auth.decorators import login_required
@login_required
def staff_list(request):
    context = set_config(request)
    user = request.user
    # Get HOD staff object
    try:
        hod_staff = Staff.objects.get(user=user)
        department = hod_staff.department
        staff_members = Staff.objects.filter(department=department).exclude(id=hod_staff.id)
    except Staff.DoesNotExist:
        staff_members = Staff.objects.none()
    # Ensure each staff has an email, fallback to user.email if not set
    for staff in staff_members:
        if not staff.email and staff.user and hasattr(staff.user, 'email') and staff.user.email:
            staff.email = staff.user.email
        # Fallback for mobile
        if (not staff.mobile or staff.mobile == '') and staff.user and hasattr(staff.user, 'mobile') and staff.user.mobile:
            staff.mobile = staff.user.mobile
    context['staff_members'] = staff_members
    return render(request, 'staff_list.html', context)

from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import get_user_model
from django.utils import timezone
import random
from django.core.mail import send_mail
from django.conf import settings

# View for HOD to see all staff in their department
from django.contrib.auth.decorators import login_required

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import BONAFIDE, GATEPASS, Staff, AHOD, HOD, Notification, Student
from .models import SemesterSubject
from django.db import models
# Principal dashboard view
@login_required
@user_passes_test(lambda u: hasattr(u, 'principal_status') and u.principal_status, login_url='/login/')
def principal_dashboard(request):
    return render(request, 'principal/dashboard.html', {})



# Period-wise attendance view
from django.http import HttpResponse
@login_required
def period_attendance_view(request):
    context = set_config(request)
    selected_date = request.GET.get('date')
    roll = request.GET.get('roll')
    period_attendance = {}
    student = None
    error = None
    if roll:
        student = Student.objects.filter(roll=roll).first()
    else:
        student = context.get('duser')
    if not isinstance(student, Student):
        error = 'Student not found.'
    elif selected_date:
        # Show 7 periods for the selected date (placeholder data)
        period_attendance = {}
        for i in range(1, 8):
            period_attendance[f'Period {i}'] = {
                'status': 'Present' if i % 2 == 1 else 'Absent',
                'marked_by': f'Staff {chr(64+i)}',
                'remarks': '' if i != 2 else 'Medical',
            }
    context['selected_date'] = selected_date
    context['student'] = student
    context['period_attendance'] = period_attendance
    context['error'] = error
    return render(request, 'student/period_attendance.html', context)

# Student attendance view for date-wise lookup
@login_required
def staff_attendance_view(request):
    context = set_config(request)
    staff = None
    assigned_subjects = []
    subjects_with_students = []
    try:
        staff = Staff.objects.get(user=request.user)
        assigned_subjects = SemesterSubject.objects.filter(staff=staff)
        for subject in assigned_subjects:
            # Get students in the same department and semester as the subject
            semester_obj = subject.semester
            students = Student.objects.filter(department=semester_obj.department, semester=semester_obj.semester)
            subjects_with_students.append({
                'subject': subject,
                'students': students
            })
    except Staff.DoesNotExist:
        assigned_subjects = []
    context['subjects_with_students'] = subjects_with_students
    return render(request, 'staff/attendance.html', context)
def student_attendance_view(request):
    context = set_config(request)

    from .models import Attendance, Student, SemesterSubject

    attendance_status = None
    selected_date = request.GET.get('date')
    roll = request.GET.get('roll')
    # If roll is provided, get that student, else use logged-in user
    if roll:
        student = Student.objects.filter(roll=roll).first()
    else:
        student = context.get('duser')
    if not isinstance(student, Student):
        context['attendance_status'] = None
        context['selected_date'] = selected_date
        context['attendance_map'] = {}
        context['calendar_month'] = timezone.now().month
        context['calendar_year'] = timezone.now().year
        context['student'] = None
        context['error'] = 'Student not found.'
        context['subjects'] = []
        return render(request, 'student/attendance.html', context)
    # Get all attendance records for the current month for the selected student
    today = timezone.now().date()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))
    from calendar import monthrange
    start_date = today.replace(day=1, month=month, year=year)
    end_date = today.replace(day=monthrange(year, month)[1], month=month, year=year)
    all_attendance = Attendance.objects.filter(student=student, date__range=[start_date, end_date])
    attendance_map = {a.date.strftime('%Y-%m-%d'): a.status for a in all_attendance}
    if selected_date:
        try:
            date_obj = timezone.datetime.strptime(selected_date, '%Y-%m-%d').date()
            record = Attendance.objects.filter(student=student, date=date_obj).first()
            if record:
                attendance_status = record.status
            else:
                attendance_status = None
        except Exception:
            attendance_status = None
    # Get subjects for this student: department+semester (non-electives) + assigned electives only
    subjects_qs = SemesterSubject.objects.filter(
        semester__department=student.department,
        semester__semester=student.semester,
        is_elective=False
    )
    electives = [student.elective1, student.elective2, student.elective3]
    electives = [e for e in electives if e]
    subjects = list(subjects_qs) + electives
    # Remove duplicates
    subjects = list({s.id: s for s in subjects}.values())
    # Calculate overall attendance percentage for this student (by total days marked and present)
    total_days = Attendance.objects.filter(student=student).count()
    present_days = Attendance.objects.filter(student=student, status='Present').count()
    overall_percentage = (present_days / total_days) * 100 if total_days > 0 else 0
    subject_percentages = []
    for subject in subjects:
        subject_percentages.append({
            'subject': subject,
            'percentage': overall_percentage
        })
    context['attendance_status'] = attendance_status
    context['selected_date'] = selected_date
    context['attendance_map'] = attendance_map
    context['calendar_month'] = month
    context['calendar_year'] = year
    context['student'] = student
    context['subjects'] = subjects
    context['subject_percentages'] = subject_percentages
    return render(request, 'student/attendance.html', context)

# AHOD Bonafide (HOD) requests view


@login_required
def staff_list(request):
    context = set_config(request)
    user = request.user
    # Get HOD staff object
    try:
        hod_staff = Staff.objects.get(user=user)
        department = hod_staff.department
        staff_members = Staff.objects.filter(department=department).exclude(id=hod_staff.id).order_by('name')
    except Staff.DoesNotExist:
        staff_members = Staff.objects.none()
    # Ensure each staff has an email, fallback to user.email if not set
    for staff in staff_members:
        if not staff.email and staff.user and hasattr(staff.user, 'email') and staff.user.email:
            staff.email = staff.user.email
        # Fallback for mobile
        if (not staff.mobile or staff.mobile == '') and staff.user and hasattr(staff.user, 'mobile') and staff.user.mobile:
            staff.mobile = staff.user.mobile
    context['staff_members'] = staff_members
    return render(request, 'hod/staff_list.html', context)

# AHOD Bonafide (HOD) requests view

@login_required
def ahod_bonafide_hod(request):
    context = set_config(request)
    ahod = AHOD.objects.filter(user=context['duser']).first()
    # Get HODs in the same department as AHOD
    hods = HOD.objects.filter(department=ahod.department) if ahod else HOD.objects.none()
    hod_staff_ids = [h.user.id for h in hods]
    # Get bonafide requests assigned to HODs in this department, pending HOD action
    bonafide_forms = BONAFIDE.objects.filter(user__hod_id__in=hod_staff_ids).distinct()
    # Only show requests where the mentor is the current AHOD (not HODs as mentor)
    mentee_bonafide_forms = BONAFIDE.objects.filter(user__mentor_id=context['duser'].id).distinct()
    context['bonafide_forms'] = bonafide_forms
    context['mentee_bonafide_forms'] = mentee_bonafide_forms
    if request.method == 'POST':
        bonafide_id = request.POST.get('bonafide_id')
        action = request.POST.get('action') or request.POST.get('sts')
        reason = request.POST.get('reason')
        role = request.POST.get('role')
        bonafide = BONAFIDE.objects.get(id=bonafide_id)
        if role == 'mentor':
            if action == 'Approved':
                bonafide.Mstatus = 'Approved by AHOD'
            elif action == 'Rejected':
                bonafide.Mstatus = 'Rejected by AHOD'
            bonafide.ahod_reason = reason
            bonafide.save()
            Notification.objects.create(
                student=bonafide.user,
                message=f"Your Bonafide request was {bonafide.Mstatus} (Reason: {reason})"
            )
        else:
            if action == 'approve':
                bonafide.Hstatus = 'Approved by AHOD'
            elif action == 'reject':
                # If AHOD rejects for HOD role, reject all statuses and notify all
                bonafide.Hstatus = 'Rejected by AHOD'
                bonafide.Mstatus = 'Rejected by AHOD'
                bonafide.Astatus = 'Rejected by AHOD'
                bonafide.ahod_reason = reason
                bonafide.save()
                # Notify student
                Notification.objects.create(
                    student=bonafide.user,
                    message=f"Your Bonafide request was {bonafide.Hstatus} (Reason: {reason})"
                )
                # Notify mentor if exists
                if bonafide.user.mentor:
                    Notification.objects.create(
                        staff=bonafide.user.mentor,
                        role='mentor',
                        message=f"Bonafide request for {bonafide.user.name} was rejected by AHOD."
                    )
                # Notify advisor if exists
                if bonafide.user.advisor:
                    Notification.objects.create(
                        staff=bonafide.user.advisor,
                        role='advisor',
                        message=f"Bonafide request for {bonafide.user.name} was rejected by AHOD."
                    )
                return redirect('ahod_bonafide_hod')
            bonafide.ahod_reason = reason
            bonafide.save()
            Notification.objects.create(
                student=bonafide.user,
                message=f"Your Bonafide request was {bonafide.Hstatus} (Reason: {reason})"
            )
        return redirect('ahod_bonafide_hod')
    return render(request, 'ahod/bonafide_hod.html', context)

# AHOD Gatepass (HOD) requests view
@login_required
def ahod_gatepass_hod(request):
    context = set_config(request)
    ahod = AHOD.objects.filter(user=context['duser']).first()
    hods = HOD.objects.filter(department=ahod.department) if ahod else HOD.objects.none()
    hod_staff_ids = [h.user.id for h in hods]
    gatepass_forms = GATEPASS.objects.filter(user__hod_id__in=hod_staff_ids).distinct()
    # Only show requests where the mentor is the current AHOD (not HODs as mentor)
    mentee_gatepass_forms = GATEPASS.objects.filter(user__mentor_id=context['duser'].id).distinct()
    context['gatepass_forms'] = gatepass_forms
    context['mentee_gatepass_forms'] = mentee_gatepass_forms
    if request.method == 'POST':
        gatepass_id = request.POST.get('gatepass_id')
        action = request.POST.get('action') or request.POST.get('sts')
        reason = request.POST.get('reason')
        role = request.POST.get('role')
        gatepass = GATEPASS.objects.get(id=gatepass_id)
        if role == 'mentor':
            if action == 'Approved':
                gatepass.Mstatus = 'Approved by AHOD'
            elif action == 'Rejected':
                gatepass.Mstatus = 'Rejected by AHOD'
            gatepass.ahod_reason = reason
            gatepass.save()
            Notification.objects.create(
                student=gatepass.user,
                message=f"Your Gatepass request was {gatepass.Mstatus} (Reason: {reason})"
            )
        else:
            if action == 'approve':
                # Set all statuses to 'Approved' so HOD table reflects the change
                gatepass.Hstatus = 'Approved'
                gatepass.Mstatus = 'Approved'
                gatepass.Astatus = 'Approved'
            elif action == 'reject':
                # If AHOD rejects for HOD role, reject all statuses and notify all
                gatepass.Hstatus = 'Rejected'
                gatepass.Mstatus = 'Rejected'
                gatepass.Astatus = 'Rejected'
                gatepass.ahod_reason = reason
                gatepass.save()
                # Notify student
                Notification.objects.create(
                    student=gatepass.user,
                    message=f"Your Gatepass request was {gatepass.Hstatus} (Reason: {reason})"
                )
                # Notify mentor if exists
                if gatepass.user.mentor:
                    Notification.objects.create(
                        staff=gatepass.user.mentor,
                        role='mentor',
                        message=f"Gatepass request for {gatepass.user.name} was rejected by AHOD."
                    )
                # Notify advisor if exists
                if gatepass.user.advisor:
                    Notification.objects.create(
                        staff=gatepass.user.advisor,
                        role='advisor',
                        message=f"Gatepass request for {gatepass.user.name} was rejected by AHOD."
                    )
                return redirect('ahod_gatepass_hod')
            gatepass.ahod_reason = reason
            gatepass.save()
            Notification.objects.create(
                student=gatepass.user,
                message=f"Your Gatepass request was {gatepass.Hstatus} (Reason: {reason})"
            )
        return redirect('ahod_gatepass_hod')
    return render(request, 'ahod/gatepass_hod.html', context)
# ...existing code...
from django.shortcuts import render
from .models import Notification, Staff
from django.contrib.auth.decorators import login_required
@login_required
def ahod_notification_history(request):
    ahod = None
    if hasattr(request, 'duser'):
        ahod = getattr(request, 'duser', None)
    if not ahod:
        try:
            ahod = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            ahod = None
    # Only allow AHODs
    if not ahod or not hasattr(ahod, 'position2') or ahod.position2 != 1:
        return render(request, 'ahod/notification_history.html', {'all_notifications': [], 'duser': ahod})
    # Query notifications for AHOD
    all_notifications = Notification.objects.filter(staff=ahod, role__iexact='ahod').order_by('-created_at')
    if request.method == "POST" and 'delete_all' in request.POST:
        all_notifications.delete()
        return redirect('hod_notification_history')
    elif request.method == "POST":
        all_notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'ahod/notification_history.html', {
        'all_notifications': all_notifications,
        'duser': ahod
    })

# View to handle delete all notifications POST
@login_required
def delete_all_notifications(request):
    ahod = None
    if hasattr(request, 'duser'):
        ahod = getattr(request, 'duser', None)
    if not ahod:
        try:
            ahod = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            ahod = None
    if not ahod or not hasattr(ahod, 'position2') or ahod.position2 != 1:
        return redirect('hod_notification_history')
    Notification.objects.filter(staff=ahod, role__iexact='ahod').delete()
    return redirect('hod_notification_history')


@login_required
def my_class_students(request):
    from .models import Attendance
    from django.utils import timezone
    staff = Staff.objects.get(user=request.user)
    students = Student.objects.filter(advisor=staff).order_by('roll')
    context = {
        'students': students,
        'duser': staff,
    }
    selected_date = None
    if request.method == 'POST':
        date_str = request.POST.get('attendance_date')
        error_msg = None
        success_msg = None
        if date_str:
            try:
                selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except Exception:
                selected_date = timezone.now().date()
        else:
            selected_date = timezone.now().date()

        # Debug: print students
        print('DEBUG: students:', list(students))

        if not students:
            error_msg = 'No students found for your class.'
        else:
            # Parse last 3 digits input for absent students
            absent_last3 = request.POST.get('absent_last3', '')
            absent_last3 = absent_last3.replace(',', ' ').split()
            absent_last3 = [x.strip() for x in absent_last3 if x.strip().isdigit() and len(x.strip()) == 3]
            absent_set = set(absent_last3)

            # Find students whose roll ends with any of the absent last 3 digits
            absent_students = [s for s in students if s.roll and s.roll[-3:] in absent_set]
            absent_ids = set(s.id for s in absent_students)

            # Mark attendance for each student (no subject)
            for student in students:
                Attendance.objects.update_or_create(
                    student=student,
                    date=selected_date,
                    defaults={'status': 'Absent' if student.id in absent_ids else 'Present'}
                )

            # Recalculate present percentage for each student (overall)
            for student in students:
                total_days = Attendance.objects.filter(student=student).count()
                present_days = Attendance.objects.filter(student=student, status='Present').count()
                percentage = (present_days / total_days) * 100 if total_days > 0 else 0
                latest_attendance = Attendance.objects.filter(student=student).order_by('-date').first()
                if latest_attendance:
                    latest_attendance.percentage = percentage
                    latest_attendance.save(update_fields=['percentage'])

            # Now recalculate student_percentages for display
            student_percentages = {}
            for student in students:
                total_days = Attendance.objects.filter(student=student).count()
                present_days = Attendance.objects.filter(student=student, status='Present').count()
                percentage = (present_days / total_days) * 100 if total_days > 0 else 0
                student_percentages[student.id] = percentage
            context['student_percentages'] = student_percentages
            success_msg = 'Attendance marked successfully.'
        context['error'] = error_msg
        context['success'] = success_msg
        context['selected_date'] = date_str
    else:
        # GET: recalculate student_percentages for display
        student_percentages = {}
        for student in students:
            total_days = Attendance.objects.filter(student=student).count()
            present_days = Attendance.objects.filter(student=student, status='Present').count()
            percentage = (present_days / total_days) * 100 if total_days > 0 else 0
            student_percentages[student.id] = percentage
        context['student_percentages'] = student_percentages
        context['selected_date'] = ''
    return render(request, 'staff/my_class_students.html', context)

@login_required
def ahod_dash(request):
    context = set_config(request)
    ahod = AHOD.objects.get(user=context['duser'])
    # Get department code for AHOD
    ahod_dept = ahod.user.department
    # Get all students in the same department as AHOD
    students = Student.objects.filter(department=ahod_dept)
    context['all_od'] = OD.objects.filter(user__in=students).distinct()
    context['all_leave'] = LEAVE.objects.filter(user__in=students).distinct()
    return render(request, 'ahod/dash.html', context)



@login_required
def hod_notification_history(request):
    staff = None
    if hasattr(request, 'duser'):
        staff = getattr(request, 'duser', None)
    if not staff:
        try:
            staff = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            staff = None
    if not staff or not hasattr(staff, 'position') or staff.position != 0:
        return render(request, 'hod/hod_notification_history.html', {'notifications': [], 'duser': staff})
    notifications = Notification.objects.filter(staff=staff, role__iexact='hod').order_by('-created_at')
    if request.method == "POST" and 'delete_all' in request.POST:
        notifications.delete()
        return redirect('hod_notification_history')
    elif request.method == "POST":
        notifications.filter(is_read=False).update(is_read=True)
    recent_notifications = notifications[:5]
    return render(request, 'hod/hod_notification_history.html', {
        'notifications': notifications,
        'recent_notifications': recent_notifications,
        'duser': staff
    })

# View to handle delete all notifications POST for HOD
@login_required
def delete_all_hod_notifications(request):
    staff = None
    if hasattr(request, 'duser'):
        staff = getattr(request, 'duser', None)
    if not staff:
        try:
            staff = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            staff = None
    if not staff or not hasattr(staff, 'position') or staff.position != 0:
        return redirect('hod_notification_history')
    Notification.objects.filter(staff=staff, role__iexact='hod').delete()
    return redirect('hod_notification_history')
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification, Student
from .models import Staff

# Student notifications view
@login_required
def notifications_view(request):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return render(request, "student/notification_history.html", {"error": "No student record found for this user."})
    latest_unread = Notification.objects.filter(student=student, is_read=False)[:5]
    all_notifications = Notification.objects.filter(student=student)
    if request.method == "POST" and 'delete_all' in request.POST:
        Notification.objects.filter(student=student).delete()
        return redirect('notifications_view')
    elif request.method == "POST":
        Notification.objects.filter(student=student, is_read=False).update(is_read=True)
    context = {
        "latest_unread": latest_unread,
        "all_notifications": all_notifications,
        "duser": student,
    }
    return render(request, "student/notification_history.html", context)

# View to handle delete all notifications POST for students
@login_required
def delete_all_student_notifications(request):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return redirect('notifications_view')
    Notification.objects.filter(student=student).delete()
    return redirect('notifications_view')

# Staff notifications view
@login_required
def staff_notifications_view(request):
    staff = None
    # Try to get staff from context if available
    if 'duser' in request.session or 'duser' in request.__dict__ or hasattr(request, 'duser'):
        staff = getattr(request, 'duser', None)
    if not staff:
        try:
            staff = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            staff = None
    if not staff:
        return redirect('login')
    # Only show HOD notifications for HOD users
    if hasattr(staff, 'position') and staff.position == 0:  # HOD position
        latest_unread = Notification.objects.filter(staff=staff, role='hod', is_read=False).order_by('-created_at')[:5]
        all_notifications = Notification.objects.filter(staff=staff, role='hod').order_by('-created_at')
        unread_count = Notification.objects.filter(staff=staff, role='hod', is_read=False).count()
    else:
        latest_unread = Notification.objects.filter(staff=staff, is_read=False).order_by('-created_at')[:5]
        all_notifications = Notification.objects.filter(staff=staff).order_by('-created_at')
        unread_count = Notification.objects.filter(staff=staff, is_read=False).count()
        if request.method == "POST" and 'delete_all' in request.POST:
            Notification.objects.filter(staff=staff).delete()
            return redirect('staff_notifications')
        elif request.method == "POST":
            Notification.objects.filter(staff=staff, is_read=False).update(is_read=True)
    return render(request, "staff/notification_history.html", {
        "latest_unread": latest_unread,
        "all_notifications": all_notifications,
        "unread_count": unread_count,
        "duser": staff,
    })


# View to handle delete all notifications POST for staff
@login_required
def delete_all_staff_notifications(request):
    staff = None
    if hasattr(request, 'duser'):
        staff = getattr(request, 'duser', None)
    if not staff:
        try:
            staff = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            staff = None
    if not staff:
        return redirect('login')
    Notification.objects.filter(staff=staff).delete()
    return redirect('staff_notifications')

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


@login_required
def ahod_od_view(request):
    context = set_config(request)
    from .models import Staff, AHOD, OD
    from django.db.models import Q
    try:
        duser = Staff.objects.get(user=request.user)
    except Staff.DoesNotExist:
        duser = None
    context['duser'] = duser
    ahod = AHOD.objects.filter(user=duser).first() if duser else None
    # Mentees: ODs where duser is mentor or advisor
    context['mods'] = OD.objects.filter(Q(user__mentor=duser) | Q(user__advisor=duser)).distinct()
    # Dept ODs: all ODs for students in AHOD's department
    if ahod and hasattr(ahod, 'user') and hasattr(ahod.user, 'department'):
        context['hods'] = OD.objects.filter(user__department=ahod.user.department).distinct()
    else:
        context['hods'] = OD.objects.none()
    return render(request, 'ahod/ods.html', context)

@login_required
def ahod_leave_view(request):
    from django.db.models import Q
    context = set_config(request)
    ahod = AHOD.objects.get(user=context['duser'])
    # Mentees: students where AHOD is mentor
    context['mods'] = LEAVE.objects.filter(user__mentor=ahod.user)
    # Dept leaves: all leaves for students in AHOD's department (match ODs logic)
    dept = getattr(ahod.user, 'department', None)
    if dept:
        context['hods'] = LEAVE.objects.filter(user__department=dept).order_by('-created')
    else:
        context['hods'] = LEAVE.objects.none()
    return render(request, 'ahod/leaves.html', context)

# Student Profile View
@login_required
def student_profile(request):
    from .models import AHOD, HOD
    context = set_config(request)
    student = context.get('duser')
    dept_ahod = None
    dept_hod = None
    # Prefer direct relation if set
    if hasattr(student, 'ahod') and student.ahod:
        dept_ahod = student.ahod
    if hasattr(student, 'hod') and student.hod:
        dept_hod = HOD.objects.filter(user=student.hod).first()
    # Fallback to department match if not set
    if not dept_ahod or not dept_hod:
        if hasattr(student, 'department') and student.department is not None:
            try:
                dept_code = int(student.department)
                if not dept_ahod:
                    dept_ahod = AHOD.objects.filter(department=dept_code).first()
                if not dept_hod:
                    dept_hod = HOD.objects.filter(department=dept_code).first()
            except Exception:
                pass
    context['dept_ahod'] = dept_ahod
    context['dept_hod'] = dept_hod
    return render(request, 'common/profile.html', context)


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

    # --- Add today's timetable for staff dashboard ---
    if request.user.is_staff:
        from core.services.get_todays_timetable import get_todays_timetable
        context['todays_timetable'] = get_todays_timetable(context['duser'])

    if not request.user.is_staff:
        # Show only the student's own results for each section
        context['gatepasses'] = GATEPASS.objects.filter(user=context['duser'])
        context['bonafides'] = BONAFIDE.objects.filter(user=context['duser'])
        context['leaves'] = LEAVE.objects.filter(user=context['duser'])
        context['ods'] = OD.objects.filter(user=context['duser'])
        return render(request, 'student/dash.html', context=context)

    elif context['duser'].position == 0 or AHOD.objects.filter(user=context['duser']).exists() or context['duser'].position2 == 1:
        # HOD or AHOD or Assistant Head of Department
        context['allratings'] = IndividualStaffRating.objects.all()
        # If HOD, use HOD logic
        if context['duser'].position == 0:
            hod = HOD.objects.get(user=context['duser'])
            staff_list = [i for i in hod.staffs.all()]
            ratings = map_feedback(staff_list)
            context['ratings'] = ratings
            temp = IndividualStaffRating.objects.all()
            rating_logs = []
            for i in temp:
                if i.staff.department == context['duser'].department:
                    rating_logs.append(i)
            context['my_rating'] = ratings.get(context['duser'].name, None)
            context['rating_log'] = rating_logs[:len(ratings)]
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
        # If AHOD or Assistant HOD, show all student applications for their department
        else:
            # Find the AHOD object for this user
            ahod = AHOD.objects.filter(user=context['duser']).first()
            if ahod:
                staff_list = list(ahod.staffs.all())
                staff_list.append(ahod.user)
            else:
                staff_list = [context['duser']]
            context['all_od'] = OD.objects.filter(
                models.Q(user__advisor__in=staff_list) |
                models.Q(user__mentor__in=staff_list) |
                models.Q(user__hod__in=staff_list)
            ).distinct()
            context['all_leave'] = LEAVE.objects.filter(
                models.Q(user__advisor__in=staff_list) |
                models.Q(user__mentor__in=staff_list) |
                models.Q(user__hod__in=staff_list)
            ).distinct()
            return render(request, "ahod/dash.html", context)

    else:
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        one_day_ago = now - timedelta(days=1)
        staff = context['duser']
        # Fetch all mentee requests for all forms where user is mentor, advisor, or HOD
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
        # All mentee requests for all forms
        context['mentee_ods'] = OD.objects.filter(
            models.Q(user__advisor=staff) | models.Q(user__mentor=staff) | models.Q(user__hod=staff)
        ).distinct()
        context['mentee_leaves'] = LEAVE.objects.filter(
            models.Q(user__advisor=staff) | models.Q(user__mentor=staff) | models.Q(user__hod=staff)
        ).distinct()
        context['mentee_gatepasses'] = GATEPASS.objects.filter(
            models.Q(user__advisor=staff) | models.Q(user__mentor=staff) | models.Q(user__hod=staff)
        ).distinct()
        context['mentee_bonafides'] = BONAFIDE.objects.filter(
            models.Q(user__advisor=staff) | models.Q(user__mentor=staff) | models.Q(user__hod=staff)
        ).distinct()
        return render(request, 'staff/dash.html', context)



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

from django.views.decorators.cache import never_cache

@login_required
@never_cache
def logout_user(request):
    logout(request)
    response = redirect('dash')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

# HOD MODULE
@login_required


def od(request):
    context = set_config(request)

    if request.method == "POST":
        sub = get_post(request, 'sub')
        body = get_post(request, 'reason')
        start = get_post(request, 'start')
        end = get_post(request, 'end')
        proof = request.FILES.get('proof')

        # Convert browser datetime string → Python datetime
        start = parse_datetime(start)
        end = parse_datetime(end)
        from django.utils import timezone
        if start and timezone.is_naive(start):
            start = timezone.make_aware(start)
        if end and timezone.is_naive(end):
            end = timezone.make_aware(end)

        # Create OD request
        obj = OD.objects.create(
            user=context['duser'],
            sub=sub,
            body=body,
            start=start,
            end=end,
            proof=proof
        )

        # Notify mentor, advisor, HOD, AHOD
        student = context['duser']
        staff_list = [
            (student.mentor, 'mentor'),
            (student.advisor, 'advisor'),
            (student.hod, 'hod'),
            (student.ahod.user if student.ahod else None, 'ahod'),
        ]
        for staff, role in staff_list:
            if staff:
                Notification.objects.create(
                    staff=staff,
                    role=role,
                    message=f"New OD request from {student.name}"
                )

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
        # Make timezone aware if needed
        if timezone.is_naive(f):
            f = timezone.make_aware(f)
        if timezone.is_naive(t):
            t = timezone.make_aware(t)
        obj = LEAVE(user=context['duser'], sub=sub,
                    body=body, start=f, end=t, proof=proff)
        obj.save()
        # Notify mentor, advisor, HOD, AHOD
        student = context['duser']
        staff_list = [
            (student.mentor, 'mentor'),
            (student.advisor, 'advisor'),
            (student.hod, 'hod'),
            (student.ahod.user if student.ahod else None, 'ahod'),
        ]
        for staff, role in staff_list:
            if staff:
                Notification.objects.create(
                    staff=staff,
                    role=role,
                    message=f"New Leave request from {student.name}"
                )
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

        # Notify mentor, advisor, HOD
        student = context['duser']
        staff_list = [student.mentor, student.advisor, student.hod]
        for staff in staff_list:
            if staff:
                role = 'hod' if hasattr(staff, 'position') and staff.position == 0 else None
                Notification.objects.create(
                    staff=staff,
                    role=role,
                    message=f"New Gatepass request from {student.name}",
                )
    # Notify mentor, advisor, HOD, AHOD
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

    context['mods'] = [i for i in OD.objects.all() if i.user.mentor.id == context['duser'].id]
    context['hods'] = [i for i in OD.objects.all() if i.user.hod.id == context['duser'].id or i.user.mentor.id != context['duser'].id]
    # Ensure OD body is always set for all entries
    for od in context['mods'] + context['hods']:
        if not od.body:
            od.body = "No details provided."
    print(context)
    return render(request, 'hod/ods.html', context)

@login_required
def hod_leave_view(request):
    context = set_config(request)

    context['mods'] = [i for i in LEAVE.objects.all() if i.user.mentor.id == context['duser'].id]
    context['hods'] = [i for i in LEAVE.objects.all() if i.user.hod.id ==
                       context['duser'].id or i.user.mentor.id != context['duser'].id]
    print(context)
    return render(request, 'hod/leaves.html', context)

@login_required
def hod_gatepass_view(request):
    context = set_config(request)

    context['mods'] = [i for i in GATEPASS.objects.all() if i.user.mentor.id == context['duser'].id]
    context['hods'] = [i for i in GATEPASS.objects.all() if i.user.hod.id ==
                       context['duser'].id or i.user.mentor.id != context['duser'].id]
    print(context)
    return render(request, 'hod/gatepasss.html', context)

@login_required

@login_required
def staff_action_od(request, id):

    if request.POST:
        od = OD.objects.get(id=id)
        print(f"staff_action_od: mentor={od.user.mentor.user.username}, advisor={od.user.advisor.user.username}, hod={od.user.hod.user.username}, current_user={request.user}")
        role = request.POST.get('role')
        status = get_post(request, 'sts')
        if role == 'mentor' and str(od.user.mentor.user.username) == str(request.user):
            od.Mstatus = status
            if od.Mstatus == STATUS[2][0]:  # Rejected
                od.Astatus = STATUS[2][0]
                od.Hstatus = STATUS[2][0]
                od.AHstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                student=od.user,
                message=f"Your OD request was {od.Mstatus} by Mentor"
            )
            print(od.Mstatus)
            od.save()
            return redirect("staff_od_view")
        elif role == 'advisor' and str(od.user.advisor.user.username) == str(request.user):
            od.Astatus = status
            print(f"Advisor action: POST['sts']={od.Astatus}, Mentor={od.Mstatus}, Advisor={od.Astatus}, User={request.user}")
            # If advisor is also acting as mentor (mentor is still pending), update mentor status
            if od.Mstatus == STATUS[0][0]:  # Pending
                print("Advisor acting as mentor: updating Mstatus to", od.Astatus)
                od.Mstatus = od.Astatus
            # If advisor rejects, cascade rejection
            if od.Astatus == STATUS[2][0]:  # Rejected
                print("Advisor rejected: cascading rejection to Hstatus and AHstatus")
                od.Hstatus = STATUS[2][0]
                od.AHstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                student=od.user,
                message=f"Your OD request was {od.Astatus} by Advisor"
            )
            print(f"After save: Mentor={od.Mstatus}, Advisor={od.Astatus}, HOD={od.Hstatus}, AHOD={od.AHstatus}")
            od.save()
            return redirect("staff_od_view")
        elif role == 'hod' and str(od.user.hod.user.username) == str(request.user):
            action_status = status
            if action_status == STATUS[1][0]:  # 'Approved'
                od.Mstatus = STATUS[1][0]
                od.Astatus = STATUS[1][0]
                od.Hstatus = STATUS[1][0]
                od.AHstatus = STATUS[1][0]
            elif action_status == STATUS[2][0]:  # 'Rejected'
                od.Mstatus = STATUS[2][0]
                od.Astatus = STATUS[2][0]
                od.Hstatus = STATUS[2][0]
                od.AHstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                student=od.user,
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
        leave = LEAVE.objects.get(id=id)
        role = request.POST.get('role')
        status = get_post(request, 'sts')
        print(f"staff_action_leave: mentor={leave.user.mentor.user.username}, advisor={leave.user.advisor.user.username}, hod={leave.user.hod.user.username}, current_user={request.user}, role={role}, status={status}")

        if role == 'mentor' and str(leave.user.mentor.user.username) == str(request.user):
            leave.Mstatus = status
            # Only set other statuses if rejected, not approved
            if leave.Mstatus == STATUS[2][0]:  # Rejected
                leave.Astatus = STATUS[2][0]
                leave.Hstatus = STATUS[2][0]
                leave.AHstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                student=leave.user,
                message=f"Your Leave request was {leave.Mstatus} by Mentor"
            )
            print(leave.Mstatus)
        elif role == 'advisor' and str(leave.user.advisor.user.username) == str(request.user):
            leave.Astatus = status
            # If mentor is still pending, set mentor status to advisor's decision
            if leave.Mstatus == STATUS[0][0]:  # Pending
                leave.Mstatus = leave.Astatus
            if leave.Astatus == STATUS[2][0]:
                leave.Hstatus = STATUS[2][0]
                leave.AHstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                student=leave.user,
                message=f"Your Leave request was {leave.Astatus} by Advisor"
            )
        elif role == 'hod' and str(leave.user.hod.user.username) == str(request.user):
            action_status = status
            if action_status == STATUS[1][0]:  # 'Approved'
                leave.Mstatus = STATUS[1][0]
                leave.Astatus = STATUS[1][0]
                leave.Hstatus = STATUS[1][0]
                leave.AHstatus = STATUS[1][0]
            elif action_status == STATUS[2][0]:  # 'Rejected'
                leave.Mstatus = STATUS[2][0]
                leave.Astatus = STATUS[2][0]
                leave.Hstatus = STATUS[2][0]
                leave.AHstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                student=leave.user,
                message=f"Your Leave request was {action_status} by HOD"
            )
            leave.save()
            print(leave.Astatus)
            return redirect("hod_leave_view")

        leave.save()
        print("Changed")

        ref = request.META.get('HTTP_REFERER')
        if ref:
            return redirect(ref)

    return redirect("staff_leave_view")


@login_required
def staff_action_gatepass(request, id):
    if request.POST:
        gatepass = GATEPASS.objects.get(id=id)
        role = request.POST.get('role')
        status = request.POST.get('sts')
        from .models import Notification
        user_is_mentor = str(gatepass.user.mentor.user.username) == str(request.user)
        user_is_advisor = str(gatepass.user.advisor.user.username) == str(request.user)
        # If staff is both mentor and advisor, update both statuses
        if (role == 'mentor' and user_is_mentor) or (role == 'advisor' and user_is_advisor):
            if user_is_mentor and user_is_advisor:
                gatepass.Mstatus = status
                gatepass.Astatus = status
                if status == STATUS[2][0]:
                    gatepass.Hstatus = STATUS[2][0]
                Notification.objects.create(
                    student=gatepass.user,
                    message=f"Your Gatepass request was {status} by Mentor/Advisor"
                )
                gatepass.save()
                return redirect("staff_gatepass_view")
            # If only mentor
            if role == 'mentor' and user_is_mentor:
                gatepass.Mstatus = status
                if status == STATUS[2][0]:  # Rejected
                    gatepass.Astatus = STATUS[2][0]
                    gatepass.Hstatus = STATUS[2][0]
                Notification.objects.create(
                    student=gatepass.user,
                    message=f"Your Gatepass request was {gatepass.Mstatus} by Mentor"
                )
                gatepass.save()
                return redirect("staff_gatepass_view")
            # If only advisor
            if role == 'advisor' and user_is_advisor:
                gatepass.Astatus = status
                if gatepass.Mstatus == STATUS[0][0]:  # Pending
                    gatepass.Mstatus = gatepass.Astatus
                if status == STATUS[2][0]:
                    gatepass.Hstatus = STATUS[2][0]
                Notification.objects.create(
                    student=gatepass.user,
                    message=f"Your Gatepass request was {gatepass.Astatus} by Advisor"
                )
                gatepass.save()
                return redirect("staff_gatepass_view")
        # HOD action
        if role == 'hod' and str(gatepass.user.hod.user.username) == str(request.user):
            if status == STATUS[1][0]:  # Approved
                gatepass.Mstatus = STATUS[1][0]
                gatepass.Astatus = STATUS[1][0]
                gatepass.Hstatus = STATUS[1][0]
            elif status == STATUS[2][0]:  # Rejected
                gatepass.Mstatus = STATUS[2][0]
                gatepass.Astatus = STATUS[2][0]
                gatepass.Hstatus = STATUS[2][0]
            else:
                gatepass.Hstatus = status
            Notification.objects.create(
                student=gatepass.user,
                message=f"Your Gatepass request was {gatepass.Hstatus} by HOD"
            )
            gatepass.save()
            return redirect("hod_gatepass_view")
        gatepass.save()
        # Default: if not mentor/advisor/hod, stay on staff page
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
    duser = context.get('duser')
    from .models import Student
    if not isinstance(duser, Student):
        try:
            duser = Student.objects.get(user=request.user)
            context['duser'] = duser
        except Exception:
            return render(request, 'student/feedback.html', context)

    temp = list(i.id for i in duser.teaching_staffs.all())
    context['s_rating'] = []
    context['cs_rating'] = []
    
    hod = HOD.objects.get(user=duser.hod)

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

        # --- Feedback completion notification logic ---
        # Get all students assigned to this staff for the same class/section/year
        staff_obj = context['c_staff']
        # Find students assigned to this staff (same year/section)
        assigned_students = Student.objects.filter(
            year=staff_obj.year,
            section=staff_obj.section,
            teaching_staffs=staff_obj
        )
        # Count how many have submitted feedback for this staff
        completed_count = 0
        for student in assigned_students:
            # Check if student has feedbacked this staff
            if IndividualStaffRating.objects.filter(staff=staff_obj, student=student, is_feedbacked=True).exists():
                completed_count += 1
        if completed_count == assigned_students.count() and assigned_students.count() > 0:
            # Notify HOD only if not already notified for this staff
            hod_staff = staff_obj.hod
            msg = f"Feedback for Dr. {staff_obj.name} is completed by all assigned students."
            if not Notification.objects.filter(staff=hod_staff, role='hod', message__icontains=staff_obj.name).exists():
                Notification.objects.create(
                    staff=hod_staff,
                    role='hod',
                    message=msg
                )
        # --- End feedback completion notification logic ---
        return redirect('student_feedback')

    return render(request, "feedbackform.html", context=context)

# END HOD MODULE

# CSFW


# EDC

# Bonafide View
@login_required
def bonafide_view(request):
    context = set_config(request)
    # Ensure duser is a Student instance
    duser = context.get('duser')
    from .models import Student
    if not isinstance(duser, Student):
        try:
            duser = Student.objects.get(name=duser)
            context['duser'] = duser
        except Exception:
            context['bonafides'] = BONAFIDE.objects.none()
        else:
            context['bonafides'] = BONAFIDE.objects.filter(user=duser)
    else:
        context['bonafides'] = BONAFIDE.objects.filter(user=duser)
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

        # Notify mentor, advisor, HOD
        student = context['duser']
        staff_list = [student.mentor, student.advisor, student.hod]
        for staff in staff_list:
            if staff:
                role = 'hod' if hasattr(staff, 'position') and staff.position == 0 else None
                Notification.objects.create(
                    staff=staff,
                    role=role,
                    message=f"New Bonafide request from {student.name}",
                )
    # Notify mentor, advisor, HOD, AHOD
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
        role = request.POST.get('role')
        status = request.POST.get('sts')
        from .models import Notification
        user_is_mentor = str(bonafide.user.mentor.user.username) == str(request.user)
        user_is_advisor = str(bonafide.user.advisor.user.username) == str(request.user)
        # If staff is both mentor and advisor, update both statuses
        if (role == 'mentor' and user_is_mentor) or (role == 'advisor' and user_is_advisor):
            # If staff is both mentor and advisor for this student
            if user_is_mentor and user_is_advisor:
                bonafide.Mstatus = status
                bonafide.Astatus = status
                # Only set Hstatus if rejected
                if status == STATUS[2][0]:
                    bonafide.Hstatus = STATUS[2][0]
                Notification.objects.create(
                    student=bonafide.user,
                    message=f"Your Bonafide request was {status} by Mentor/Advisor"
                )
                bonafide.save()
                return redirect("staff_bonafides")
            # If only mentor
            if role == 'mentor' and user_is_mentor:
                bonafide.Mstatus = status
                if status == STATUS[2][0]:  # Rejected
                    bonafide.Astatus = STATUS[2][0]
                    bonafide.Hstatus = STATUS[2][0]
                Notification.objects.create(
                    student=bonafide.user,
                    message=f"Your Bonafide request was {bonafide.Mstatus} by Mentor"
                )
                bonafide.save()
                return redirect("staff_bonafides")
            # If only advisor
            if role == 'advisor' and user_is_advisor:
                bonafide.Astatus = status
                if bonafide.Mstatus == STATUS[0][0]:  # Pending
                    bonafide.Mstatus = bonafide.Astatus
                if status == STATUS[2][0]:
                    bonafide.Hstatus = STATUS[2][0]
                Notification.objects.create(
                    student=bonafide.user,
                    message=f"Your Bonafide request was {bonafide.Astatus} by Advisor"
                )
                bonafide.save()
                return redirect("staff_bonafides")
        if role == 'hod' and str(bonafide.user.hod.user.username) == str(request.user):
            if status == STATUS[1][0]:  # Approved
                bonafide.Mstatus = STATUS[1][0]
                bonafide.Astatus = STATUS[1][0]
                bonafide.Hstatus = STATUS[1][0]
            elif status == STATUS[2][0]:  # Rejected
                bonafide.Mstatus = STATUS[2][0]
                bonafide.Astatus = STATUS[2][0]
                bonafide.Hstatus = STATUS[2][0]
            Notification.objects.create(
                student=bonafide.user,
                message=f"Your Bonafide request was {bonafide.Hstatus} by HOD"
            )
            bonafide.save()
            return redirect("hod_bonafide_view")
        bonafide.save()
        return redirect("hod_bonafide_view")
def forgot_password(request):
    message = None
    error_message = None
    if request.method == 'POST':
        email = request.POST.get('email')
        user_obj = None
        try:
            user_obj = Student.objects.get(user__email=email)
        except Student.DoesNotExist:
            try:
                user_obj = Staff.objects.get(email=email)
            except Staff.DoesNotExist:
                error_message = 'Email not registered.'
        if user_obj:
            otp = str(random.randint(100000, 999999))
            request.session['reset_email'] = email
            request.session['reset_otp'] = otp
            send_mail(
                'Your OTP Code',
                f'Your OTP code is {otp}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            request.session['otp_sent'] = True
            return redirect('otp_verification')
    return render(request, 'auth/forgot_password.html', {'message': message, 'error_message': error_message})

def otp_verification(request):
    error_message = None
    success_message = None
    if request.session.get('otp_sent'):
        success_message = 'OTP has been sent to your registered email.'
        request.session.pop('otp_sent')
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        session_otp = request.session.get('reset_otp')
        if entered_otp == session_otp:
            request.session['otp_verified'] = True
            return redirect('reset_password')
        else:
            error_message = 'Invalid OTP. Please try again.'
    return render(request, 'auth/otp_verification.html', {'error_message': error_message, 'success_message': success_message})

def reset_password(request):
    error_message = None
    if not request.session.get('otp_verified'):
        return redirect('forgot_password')
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password != confirm_password:
            error_message = 'Passwords do not match.'
        else:
            email = request.session.get('reset_email')
            user_obj = None
            try:
                user_obj = Student.objects.get(user__email=email)
                user_obj.user.set_password(new_password)
                user_obj.user.save()
            except Student.DoesNotExist:
                try:
                    user_obj = Staff.objects.get(email=email)
                    user_obj.user.set_password(new_password)
                    user_obj.user.save()
                except Staff.DoesNotExist:
                    error_message = 'User not found.'
            if not error_message:
                # Clear session
                request.session.pop('reset_email', None)
                request.session.pop('reset_otp', None)
                request.session.pop('otp_verified', None)
                return redirect('login')
    return render(request, 'auth/reset_password.html', {'error_message': error_message})

def student_timetable(request):
    # Delegate to the actual student timetable view implementation
    from .student_timetable_views import student_timetable as real_student_timetable
    return real_student_timetable(request)

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def hod_action_od(request, id):
    if request.method == 'POST':
        od = OD.objects.get(id=id)
        action_status = request.POST.get('sts')
        role = request.POST.get('role')
        if role == 'mentor':
            od.Mstatus = action_status
            if action_status == STATUS[2][0]:  # Rejected
                od.Astatus = STATUS[2][0]
                od.Hstatus = STATUS[2][0]
                od.AHstatus = STATUS[2][0]
        elif role == 'hod':
            if action_status == STATUS[1][0]:  # 'Approved'
                od.Mstatus = STATUS[1][0]
                od.Astatus = STATUS[1][0]
                od.Hstatus = STATUS[1][0]
                od.AHstatus = STATUS[1][0]
            elif action_status == STATUS[2][0]:  # 'Rejected'
                od.Mstatus = STATUS[2][0]
                od.Astatus = STATUS[2][0]
                od.Hstatus = STATUS[2][0]
                od.AHstatus = STATUS[2][0]
        from .models import Notification
        Notification.objects.create(
            student=od.user,
            message=f"Your OD request was {action_status} by {'Mentor' if role == 'mentor' else 'HOD'}"
        )
        od.save()
        return redirect('hod_od_view')
    return redirect('hod_od_view')

@csrf_exempt
@login_required
def hod_action_leave(request, id):
    if request.method == 'POST':
        leave = LEAVE.objects.get(id=id)
        action_status = request.POST.get('sts')
        role = request.POST.get('role')
        if role == 'mentor':
            leave.Mstatus = action_status
            if action_status == STATUS[2][0]:  # Rejected
                leave.Astatus = STATUS[2][0]
                leave.Hstatus = STATUS[2][0]
                leave.AHstatus = STATUS[2][0]
        elif role == 'hod':
            if action_status == STATUS[1][0]:  # 'Approved'
                leave.Mstatus = STATUS[1][0]
                leave.Astatus = STATUS[1][0]
                leave.Hstatus = STATUS[1][0]
                leave.AHstatus = STATUS[1][0]
            elif action_status == STATUS[2][0]:  # 'Rejected'
                leave.Mstatus = STATUS[2][0]
                leave.Astatus = STATUS[2][0]
                leave.Hstatus = STATUS[2][0]
                leave.AHstatus = STATUS[2][0]
        from .models import Notification
        Notification.objects.create(
            student=leave.user,
            message=f"Your Leave request was {action_status} by {'Mentor' if role == 'mentor' else 'HOD'}"
        )
        leave.save()
        return redirect('hod_leave_view')
    return redirect('hod_leave_view')

@csrf_exempt
@login_required
def hod_action_gatepass(request, id):
    if request.method == 'POST':
        gatepass = GATEPASS.objects.get(id=id)
        action_status = request.POST.get('sts')
        role = request.POST.get('role')
        if role == 'mentor':
            gatepass.Mstatus = action_status
            if action_status == STATUS[2][0]:  # Rejected
                gatepass.Astatus = STATUS[2][0]
                gatepass.Hstatus = STATUS[2][0]
        elif role == 'hod':
            if action_status == STATUS[1][0]:  # 'Approved'
                gatepass.Mstatus = STATUS[1][0]
                gatepass.Astatus = STATUS[1][0]
                gatepass.Hstatus = STATUS[1][0]
            elif action_status == STATUS[2][0]:  # 'Rejected'
                gatepass.Mstatus = STATUS[2][0]
                gatepass.Astatus = STATUS[2][0]
                gatepass.Hstatus = STATUS[2][0]
        from .models import Notification
        Notification.objects.create(
            student=gatepass.user,
            message=f"Your Gatepass request was {action_status} by {'Mentor' if role == 'mentor' else 'HOD'}"
        )
        gatepass.save()
        return redirect('hod_gatepass_view')
    return redirect('hod_gatepass_view')

@csrf_exempt
@login_required
def hod_action_bonafide(request, id):
    if request.method == 'POST':
        bonafide = BONAFIDE.objects.get(id=id)
        action_status = request.POST.get('sts')
        role = request.POST.get('role')
        if role == 'mentor':
            bonafide.Mstatus = action_status
            if action_status == STATUS[2][0]:  # Rejected
                bonafide.Astatus = STATUS[2][0]
                bonafide.Hstatus = STATUS[2][0]
        elif role == 'hod':
            if action_status == STATUS[1][0]:  # 'Approved'
                bonafide.Mstatus = STATUS[1][0]
                bonafide.Astatus = STATUS[1][0]
                bonafide.Hstatus = STATUS[1][0]
            elif action_status == STATUS[2][0]:  # 'Rejected'
                bonafide.Mstatus = STATUS[2][0]
                bonafide.Astatus = STATUS[2][0]
                bonafide.Hstatus = STATUS[2][0]
        from .models import Notification
        Notification.objects.create(
            student=bonafide.user,
            message=f"Your Bonafide request was {action_status} by {'Mentor' if role == 'mentor' else 'HOD'}"
        )
        bonafide.save()
        return redirect('hod_bonafide_view')
    return redirect('hod_bonafide_view')


