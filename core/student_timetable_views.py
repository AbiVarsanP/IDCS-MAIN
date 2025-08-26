from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .helpers import set_config
from .models import Staff
from .timetable_models import StaffTimeTable

@login_required
def student_timetable(request):
    context = set_config(request)
    # Get the student's advisor or class staff
    staff = None
    if hasattr(context['duser'], 'advisor') and context['duser'].advisor:
        staff = context['duser'].advisor
    elif hasattr(context['duser'], 'mentor') and context['duser'].mentor:
        staff = context['duser'].mentor
    # Define days and periods (should match staff timetable)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    periods = ['1', '2', '3', '4', '5', '6', '7']
    table = {}
    if staff:
        try:
            timetable_obj = StaffTimeTable.objects.get(staff=staff)
            table = timetable_obj.data
        except StaffTimeTable.DoesNotExist:
            pass
    context['days'] = days
    context['periods'] = periods
    context['table'] = table
    context['staff'] = staff
    return render(request, 'student/timetable.html', context)
