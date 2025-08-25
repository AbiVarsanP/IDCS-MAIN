

from django.contrib import admin
from django.http import HttpResponse
import csv
from django import forms
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
try:
	import openpyxl
	from openpyxl.utils import get_column_letter
	has_openpyxl = True
except ImportError:
	has_openpyxl = False

from .models import Student, Staff, OD, LEAVE, GATEPASS, HOD, AHOD, StaffRating, RatingQuestions, IndividualStaffRating, SpotFeedback, BONAFIDE

def export_students_csv(modeladmin, request, queryset):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename=students.csv'
	writer = csv.writer(response)
	fields = ['id', 'user', 'roll', 'name', 'department', 'semester', 'year', 'section', 'address', 'mobile', 'parent_mobile', 'dob', 'age']
	writer.writerow(fields)
	for obj in queryset:
		writer.writerow([
			obj.id,
			obj.user.username if obj.user else '',
			obj.roll,
			obj.name,
			obj.department,
			obj.semester,
			obj.year,
			obj.section,
			obj.address,
			obj.mobile,
			obj.parent_mobile,
			obj.dob,
			obj.age
		])
	return response
export_students_csv.short_description = "Export Selected Students as CSV"

def export_students_excel(modeladmin, request, queryset):
	if not has_openpyxl:
		return HttpResponse("openpyxl is not installed.")
	from openpyxl import Workbook
	response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
	response['Content-Disposition'] = 'attachment; filename=students.xlsx'
	wb = Workbook()
	ws = wb.active
	fields = ['id', 'user', 'roll', 'name', 'department', 'semester', 'year', 'section', 'address', 'mobile', 'parent_mobile', 'dob', 'age']
	ws.append(fields)
	for obj in queryset:
		ws.append([
			obj.id,
			obj.user.username if obj.user else '',
			obj.roll,
			obj.name,
			obj.department,
			obj.semester,
			obj.year,
			obj.section,
			obj.address,
			obj.mobile,
			obj.parent_mobile,
			obj.dob,
			obj.age
		])
	wb.save(response)
	return response
export_students_excel.short_description = "Export Selected Students as Excel"


from django import forms
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages

class StudentImportForm(forms.Form):
	csv_file = forms.FileField(label="Select CSV file")

class StudentAdmin(admin.ModelAdmin):
	actions = [export_students_csv, export_students_excel]

	change_list_template = "admin/core/student_changelist.html"

	def get_urls(self):
		urls = super().get_urls()
		custom_urls = [
			path('import-students/', self.admin_site.admin_view(self.import_students), name='import-students'),
		]
		return custom_urls + urls

	def import_students(self, request):
		if request.method == "POST":
			form = StudentImportForm(request.POST, request.FILES)
			if form.is_valid():
				csv_file = form.cleaned_data['csv_file']
				import csv
				import io
				from datetime import datetime
				decoded_file = csv_file.read().decode('utf-8')
				reader = csv.DictReader(io.StringIO(decoded_file))
				created = 0
				updated = 0
				from django.contrib.auth.models import User
				for row in reader:
					username = row.get('user')
					if not username or not username.isdigit():
						continue
					user, created_user = User.objects.get_or_create(username=username)
					if created_user:
						user.set_password('123')
						user.save()
					student, created_obj = Student.objects.get_or_create(user=user)
					# Set/update all fields
					student.roll = row.get('roll')
					student.name = row.get('name')
					student.department = row.get('department')
					# Convert to int if possible, else use default
					def to_int(val, default=None):
						try:
							return int(val)
						except (TypeError, ValueError):
							return default
					student.semester = to_int(row.get('semester'), 1)
					student.year = to_int(row.get('year'), 1)
					student.section = to_int(row.get('section'), 2)
					student.address = row.get('address')
					student.mobile = to_int(row.get('mobile'))
					student.parent_mobile = to_int(row.get('parent_mobile'))
					# Parse date
					dob_val = row.get('dob')
					if dob_val:
						try:
							student.dob = datetime.strptime(dob_val, "%Y-%m-%d").date()
						except Exception:
							student.dob = None
					else:
						student.dob = None
					student.age = to_int(row.get('age'))
					student.save()
					if created_obj:
						created += 1
					else:
						updated += 1
				messages.success(request, f"Imported {created} students, updated {updated} students.")
				return redirect("..")
		else:
			form = StudentImportForm()
		return render(request, "admin/core/import_students.html", {"form": form})

admin.site.register(Student, StudentAdmin)
class StaffAdmin(admin.ModelAdmin):
	list_display = ('user', 'name', 'department', 'position', 'position2', 'position3')
	list_filter = ('department', 'position', 'position2', 'position3')
	search_fields = ('name', 'user__username')

admin.site.register(Staff, StaffAdmin)
admin.site.register(OD)
admin.site.register(LEAVE)
admin.site.register(GATEPASS)
admin.site.register(BONAFIDE)
admin.site.register(HOD)
class AHODAdmin(admin.ModelAdmin):
	list_display = ('user', 'department')
	list_filter = ('department',)

	actions = ['set_position2_ahod']

	def set_position2_ahod(self, request, queryset):
		# Set position2 to Assistant Head of the Department (1) for all linked staff
		updated = 0
		for ahod in queryset:
			if ahod.user:
				ahod.user.position2 = 1  # 1 = Assistant Head of the Department
				ahod.user.save()
				updated += 1
		self.message_user(request, f"Set position2 as Assistant Head of the Department for {updated} staff.")
	set_position2_ahod.short_description = 'Set position2 as Assistant Head of the Department for selected AHODs'

admin.site.register(AHOD, AHODAdmin)
admin.site.register(StaffRating)
admin.site.register(RatingQuestions)
admin.site.register(IndividualStaffRating)
admin.site.register(SpotFeedback)
