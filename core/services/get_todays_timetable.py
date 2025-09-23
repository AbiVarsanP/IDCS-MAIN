from django.utils import timezone
from core.timetable_models import StaffTimeTable

def get_todays_timetable(staff):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    periods = ['1', '2', '3', '4', '5', '6', '7']
    today = timezone.now().strftime('%A')
    if today not in days:
        return None
    try:
        timetable_obj = StaffTimeTable.objects.get(staff=staff)
        table = timetable_obj.data
        my_table = timetable_obj.my_timetable_data
    except StaffTimeTable.DoesNotExist:
        return None
    # Get today's periods for both tables
    today_periods = []
    for period in periods:
        key = f"{today}_{period}"
        subject = table.get(key, '')
        my_subject = my_table.get(key, '')
        today_periods.append({'period': period, 'subject': subject, 'my_subject': my_subject})
    return today_periods
