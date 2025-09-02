from django.shortcuts import render, get_object_or_404
from .models import Staff, Student
from django.contrib.auth.decorators import login_required

@login_required
def view_mentees(request, staff_id):
    staff = get_object_or_404(Staff, id=staff_id)
    mentees = Student.objects.filter(mentor=staff).order_by('name')
    return render(request, 'mentees_list.html', {'staff': staff, 'mentees': mentees})
