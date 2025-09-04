from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.urls import reverse
from django.contrib.auth import get_user_model
from .constants import *
# AcademicRecord model and related imports removed
class Department(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    hod = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True, related_name='department_hod')
    ahod = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True, related_name='department_ahod')
    staffs = models.ManyToManyField('Staff', blank=True, related_name='department_staffs')


    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update HOD model when hod is set
        from .models import HOD, AHOD, Student
        if self.hod:
            hod_obj, created = HOD.objects.get_or_create(user=self.hod, defaults={"department": self})
            if not created:
                hod_obj.department = self
                hod_obj.save()
            Student.objects.filter(department=self).update(hod=self.hod)
        # Update AHOD model when ahod is set
        if self.ahod and self.pk and self.ahod.pk:
            try:
                ahod_obj, created = AHOD.objects.get_or_create(user=self.ahod, defaults={"department": self})
                if not created:
                    ahod_obj.department = self
                    ahod_obj.save()
            except Exception:
                pass

    

# ...existing code...


# Attendance Model for Section 3.2: Track attendance, link to events/workshops/training, integrate with Leaves/ODs for deductions
class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('On Leave', 'On Leave'),
        ('On Duty', 'On Duty'),
    ]
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    reason = models.TextField(blank=True, null=True, help_text="If absent/on leave/on duty, link to Leave/OD/Bonafide/Gatepass")
    percentage = models.FloatField(default=0, help_text="Calculated overall attendance percentage")

    # Foreign keys to related models for status updates (nullable, only one used per record)
    leave = models.ForeignKey('LEAVE', on_delete=models.SET_NULL, blank=True, null=True, related_name='attendance_leaves')
    od = models.ForeignKey('OD', on_delete=models.SET_NULL, blank=True, null=True, related_name='attendance_ods')
    bonafide = models.ForeignKey('BONAFIDE', on_delete=models.SET_NULL, blank=True, null=True, related_name='attendance_bonafides')
    gatepass = models.ForeignKey('GATEPASS', on_delete=models.SET_NULL, blank=True, null=True, related_name='attendance_gatepasses')

    # Placeholder for event-specific attendance (One-to-Many to EventAttendance)
    # event_attendance = models.ForeignKey('EventAttendance', on_delete=models.SET_NULL, blank=True, null=True, related_name='attendance_events')

    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"



User = get_user_model()


class AHOD(models.Model):
    user = models.ForeignKey('Staff', on_delete=models.CASCADE)
    get_feedback = models.BooleanField(default=False)
    get_spot_feedback = models.BooleanField(default=False)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="ahod_departments")

    staffs = models.ManyToManyField('Staff', related_name='ahod_my_staffs', blank=True)
    students = models.ManyToManyField('Student', related_name='ahod_students', blank=True)
    assign_feedback = models.ManyToManyField('Staff', related_name='ahod_assign_feed', blank=True)
    spot_feedback = models.ManyToManyField('SpotFeedback', blank=True)

    def __str__(self):
        return f"AHOD: {self.user.name} - {self.user.department}"


class Notification(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name="student_notifications", null=True, blank=True)
    staff = models.ForeignKey('Staff', on_delete=models.CASCADE, related_name="staff_notifications", null=True, blank=True)

    ROLE_CHOICES = [
        ('mentor', 'Mentor'),
        ('advisor', 'Advisor'),
        ('hod', 'HOD'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']


class Student(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student')
    roll = models.CharField(max_length=8, unique=True, blank=True, null=True)
    profile = models.ImageField(upload_to='profiles', blank=True)
    name = models.CharField(max_length=50, blank=True, null=True)


    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    semester = models.PositiveIntegerField(choices=SEM, default=1, null=True)
    year = models.PositiveIntegerField(choices=YEAR, default=1, null=True)
    # Batch: Enter start year, display as 'start year - start year+4'
    batch = models.PositiveIntegerField(blank=True, null=True, help_text="Enter start year, e.g., 2020")
    # Academic Year: Enter start year, display as 'start year - start year+2'
    academic_year = models.PositiveIntegerField(blank=True, null=True, help_text="Enter start year, e.g., 2023")

    @property
    def batch_range(self):
        if self.batch:
            return f"{self.batch}-{self.batch+4}"
        return ""

    @property
    def academic_year_range(self):
        if self.academic_year:
            return f"{self.academic_year}-{self.academic_year+1}"
        return ""
    section = models.PositiveIntegerField(choices=SECTION, default=2)
    address = models.TextField(blank=True, null=True)
    mobile = models.IntegerField(blank=True, null=True)
    parent_mobile = models.IntegerField(blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)

    advisor = models.ForeignKey('Staff', blank=True, on_delete=models.DO_NOTHING, related_name='Advisor', null=True)
    a_advisor = models.ForeignKey('Staff', blank=True, on_delete=models.DO_NOTHING, related_name='A_Advisor', null=True)
    mentor = models.ForeignKey('Staff', blank=True, on_delete=models.DO_NOTHING, related_name='Mentor', null=True)
    hod = models.ForeignKey('Staff', blank=True, on_delete=models.DO_NOTHING, related_name='HOD', null=True)
    ahod = models.ForeignKey('AHOD', blank=True, on_delete=models.DO_NOTHING, related_name='AHOD', null=True)

    teaching_staffs = models.ManyToManyField('Staff', blank=True)
    elective1 = models.ForeignKey('SemesterSubject', null=True, blank=True, on_delete=models.SET_NULL, related_name='elective1_students', help_text="Select the first elective relevant to the student's department and semester.")
    elective2 = models.ForeignKey('SemesterSubject', null=True, blank=True, on_delete=models.SET_NULL, related_name='elective2_students', help_text="Select the second elective relevant to the student's department and semester.")
    elective3 = models.ForeignKey('SemesterSubject', null=True, blank=True, on_delete=models.SET_NULL, related_name='elective3_students', help_text="Select the third elective relevant to the student's department and semester.")
    feedback_for = models.ManyToManyField('IndividualStaffRating', related_name='for_staff_rating', blank=True)
    feedback_history = models.ManyToManyField('IndividualStaffRating', related_name='for_staff_rating_history', blank=True)

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def __str__(self) -> str:
        return f"{self.user.username} {self.department}-{self.year}"


    def save(self, *args, **kwargs):
        # Auto-set hod and ahod fields to department's hod and ahod if department is assigned
        if self.department:
            if self.department.hod:
                self.hod = self.department.hod
            if self.department.ahod:
                from core.models import AHOD
                ahod_instance = AHOD.objects.filter(user=self.department.ahod).first()
                if ahod_instance:
                    self.ahod = ahod_instance
        super().save(*args, **kwargs)

    def feedback_clear(self):
        self.feedback_for.clear()
        return True


class Staff(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff')
    name = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(max_length=254, blank=True, null=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='staffsstaff_members')
    mobile = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=50, blank=True, null=True)

    # Retain other fields for backward compatibility
    profile = models.ImageField(upload_to='profiles', blank=True)
    address = models.TextField(blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    position = models.PositiveIntegerField(choices=POS, default=0)
    position2 = models.PositiveIntegerField(choices=POS, default=0, blank=True, null=True)
    position3 = models.PositiveIntegerField(choices=POS, default=0, blank=True, null=True)
    my_feedbacks = models.ManyToManyField('IndividualStaffRating', related_name='my_ratings', blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def __str__(self) -> str:
        dept_name = self.department.name if self.department else "No Department"
        return f"{self.name} {self.user.username} {dept_name}"


class HOD(models.Model):
    user = models.ForeignKey('Staff', on_delete=models.CASCADE)
    get_feedback = models.BooleanField(default=False)
    get_spot_feedback = models.BooleanField(default=False)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='hods')

    staffs = models.ManyToManyField('Staff', related_name='my_staffs', blank=True)
    students = models.ManyToManyField('Student', related_name='students', blank=True)
    assign_feedback = models.ManyToManyField('Staff', related_name='assign_feed', blank=True)
    spot_feedback = models.ManyToManyField('SpotFeedback', blank=True)

    def __str__(self) -> str:
        return f"{self.user.name} - {self.user.department}"


class OD(models.Model):
    user = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='s_student')
    sub = models.CharField(max_length=150)
    body = models.TextField()
    start = models.DateTimeField(verbose_name="From-Date")
    end = models.DateTimeField(verbose_name="To-Date")
    proof = models.FileField(upload_to='od/proof', blank=True)
    certificate = models.FileField(upload_to='od/proof/certificate', blank=True)

    Astatus = models.CharField(choices=STATUS, max_length=50, default="Pending")
    Mstatus = models.CharField(choices=STATUS, max_length=50, default="Pending")
    Hstatus = models.CharField(choices=STATUS, max_length=50, default="Pending")
    AHstatus = models.CharField(choices=STATUS, max_length=50, default="Pending")  # AHOD approval status


    ahod_hod_action = models.CharField(max_length=50, blank=True, null=True)  # For AHOD & HOD joint action
    ahod_hod_reason = models.TextField(blank=True, null=True)  # Reason for AHOD & HOD joint action
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def __str__(self) -> str:
        return f"{self.user.name} {self.sub}"


class LEAVE(models.Model):
    user = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='sl_student')
    sub = models.CharField(max_length=150)
    body = models.TextField()
    start = models.DateTimeField(verbose_name="From-Date")
    end = models.DateTimeField(verbose_name="To-Date")
    proof = models.FileField(upload_to='leave/proof', blank=True)
    certificate = models.FileField(upload_to='leave/proof/certificate', blank=True)

    Astatus = models.CharField(choices=STATUS, max_length=50, default="Pending")
    Mstatus = models.CharField(choices=STATUS, max_length=50, default="Pending")
    Hstatus = models.CharField(choices=STATUS, max_length=50, default="Pending")
    AHstatus = models.CharField(choices=STATUS, max_length=50, default="Pending")  # AHOD approval status

    ahod_hod_action = models.CharField(max_length=50, blank=True, null=True)  # For AHOD & HOD joint action
    ahod_hod_reason = models.TextField(blank=True, null=True)  # Reason for AHOD & HOD joint action
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def __str__(self) -> str:
        return f"{self.user.name} {self.sub}"


class BONAFIDE(models.Model):
    user = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='bonafide_student')
    reason = models.CharField(max_length=255, blank=True, null=True)  # keep or rename
    body = models.TextField(blank=True, null=True)
    proof = models.FileField(upload_to='bonafide/proof', blank=True)
    certificate = models.FileField(upload_to='bonafide/proof/certificate', blank=True)


    # Add these ↓
    sub = models.CharField(max_length=255)   # Purpose
    date = models.DateField(null=True, blank=True)
    ahod_reason = models.TextField(blank=True, null=True)  # Reason by AHOD for HOD action

    Astatus = models.CharField(choices=STATUS, max_length=50, default="Pending")
    Mstatus = models.CharField(choices=STATUS, max_length=50, default="Pending")
    Hstatus = models.CharField(choices=STATUS, max_length=50, default="Pending")


    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def __str__(self) -> str:
        return f"{self.user.name} {self.sub}"



class GATEPASS(models.Model):
    user = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='sg_student')
    sub = models.CharField(max_length=150)
    start = models.DateTimeField(verbose_name="From-Date")
    end = models.DateTimeField(verbose_name="To-Date")


    Astatus = models.CharField(choices=STATUS, max_length=50, default="Pending")
    Mstatus = models.CharField(choices=STATUS, max_length=50, default="Pending")
    Hstatus = models.CharField(choices=STATUS, max_length=50, default="Pending")
    ahod_reason = models.TextField(blank=True, null=True)  # Reason by AHOD for HOD action


    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def __str__(self) -> str:
        return f"{self.user.name} {self.sub}"


class RatingQuestions(models.Model):
    user = models.ForeignKey(HOD, on_delete=models.CASCADE)
    ques = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.ques}"


class StaffRating(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    ques = models.ForeignKey(RatingQuestions, null=True, blank=True, on_delete=models.CASCADE)
    points = models.PositiveIntegerField(default=0)
    comments = models.CharField(max_length=100, default="Nill")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.staff.name} - {str(self.points)}"


class IndividualStaffRating(models.Model):
    staff = models.ForeignKey('Staff', on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    ratings = models.ManyToManyField('StaffRating', related_name='StaffRating_Individual', blank=True)
    is_feedbacked = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.staff.name} - {self.avg()}"

    def avg(self):
        inr = self.ratings.all()
        if not inr:
            return 0
        return round(sum(i.points for i in inr) / len(inr))


class Semester(models.Model):
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='semesters')
    semester = models.PositiveIntegerField(choices=SEM, default=1, null=True)
    # Subjects are now managed by SemesterSubject model

class SemesterSubject(models.Model):
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=100)
    staff = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True, related_name='semester_subject_staff')
    is_elective = models.BooleanField(default=False, help_text="Check if this subject is an elective.")

    def __str__(self):
        return f"{self.name} ({self.semester})"

    class Meta:
        unique_together = ("semester", "name")
        ordering = ["semester"]

    def __str__(self):
        dept_name = self.semester.department.name if self.semester and self.semester.department else "No Department"
        return f"{dept_name} - Semester {self.semester.semester} - {self.name}"

class SpotFeedback(models.Model):
    user = models.ForeignKey('Staff', on_delete=models.CASCADE, related_name='hod_spot')
    staff = models.ForeignKey('Staff', on_delete=models.CASCADE, related_name='staff_spot')
    year = models.PositiveIntegerField(choices=YEAR, default=1, null=True)
    section = models.PositiveIntegerField(choices=SECTION, default=2)

    feebacks = models.ManyToManyField('IndividualStaffRating', blank=True)
    is_open = models.BooleanField(default=False)
    students = models.ManyToManyField('Student', blank=True)
    completed_students = models.ManyToManyField('Student', blank=True, related_name='c_std')
    created = models.DateTimeField(auto_now_add=True)

    qr_code = models.ImageField(upload_to='Spot/qrcodes/', blank=True)
    url = models.URLField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.staff.name} - {self.avg()}"

    def avg(self):
        inr = self.feebacks.all()
        if not inr:
            return 0
        return round(sum(i.avg() for i in inr) / len(inr))

    def get_cls(self):
        return [SECTION[self.section], YEAR[self.year - 1]]

    def get_absolute_url(self):
        return reverse('student_feedback_form', args=[str(self.staff.id), 'spf'])
