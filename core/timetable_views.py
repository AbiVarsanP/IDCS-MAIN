from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .helpers import set_config
from .timetable_models import StaffTimeTable
import logging

logger = logging.getLogger(__name__)

@login_required
def staff_timetable(request):
    context = set_config(request)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    periods = ['1', '2', '3', '4', '5', '6', '7']
    staff = context['duser']
    table = {}
    my_table = {}
    try:
        timetable_obj = StaffTimeTable.objects.get(staff=staff)
        table = timetable_obj.data
        my_table = timetable_obj.my_timetable_data
    except StaffTimeTable.DoesNotExist:
        timetable_obj = None
    if request.method == 'POST':
        # Determine which form was submitted
        if 'my-edit-btn' in request.POST or 'my-save-btn' in request.POST or any(k.startswith('my_') for k in request.POST.keys()):
            # My Timetable form
            for day in days:
                for period in periods:
                    key = f"{day}_{period}"
                    my_key = f"my_{key}"
                    my_table[key] = request.POST.get(my_key, '')
            StaffTimeTable.objects.update_or_create(staff=staff, defaults={'my_timetable_data': my_table, 'data': table})
            context['my_message'] = 'My Timetable updated!'
        else:
            # Main timetable form
            for day in days:
                for period in periods:
                    key = f"{day}_{period}"
                    table[key] = request.POST.get(key, '')
            StaffTimeTable.objects.update_or_create(staff=staff, defaults={'data': table, 'my_timetable_data': my_table})
            context['message'] = 'Timetable updated!'
    # Get department subjects for dropdown
    department = getattr(staff, 'department', None)
    department_subjects = []
    if department:
        from .models import SemesterSubject, Semester
        semesters = Semester.objects.filter(department=department)
        department_subjects = SemesterSubject.objects.filter(semester__in=semesters)
    context['assigned_subjects'] = department_subjects
    context['days'] = days
    context['periods'] = periods
    context['table'] = table
    context['my_table'] = my_table
    return render(request, 'staff/timetable.html', context)

@login_required
def hod_timetable(request):
    context = set_config(request)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    periods = ['1', '2', '3', '4', '5', '6', '7']
    hod = context['duser']
    table = {}
    my_table = {}
    try:
        timetable_obj = StaffTimeTable.objects.get(staff=hod)
        table = timetable_obj.data
        my_table = timetable_obj.my_timetable_data
    except StaffTimeTable.DoesNotExist:
        timetable_obj = None

    if request.method == 'POST':
        for day in days:
            for period in periods:
                key = f"{day}_{period}"
                my_key = f"my_{key}"
                my_table[key] = request.POST.get(my_key, '')
        StaffTimeTable.objects.update_or_create(staff=hod, defaults={'my_timetable_data': my_table, 'data': table})
        context['message'] = 'HOD Timetable updated!'

    context['days'] = days
    context['periods'] = periods
    context['table'] = table
    context['my_table'] = my_table
    return render(request, 'hod/timetable.html', context)
