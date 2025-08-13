from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from .constants import *


class Student(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='student')
    roll = models.CharField(max_length=8,unique=True,blank=True,null=True)
    profile = models.ImageField(upload_to='profiles',blank=True)
    name = models.CharField(max_length=50,blank=True,null=True)
    
    department = models.CharField(choices=DEPT,default="001",max_length=50,null=True)
    semester = models.PositiveIntegerField(choices=SEM,default=1,null=True)
    year = models.PositiveIntegerField(choices=YEAR,default=1,null=True)
    section = models.PositiveIntegerField(choices=SECTION,default=2)
    address = models.TextField(blank=True,null=True)
    mobile = models.IntegerField(blank=True,null=True)
    parent_mobile = models.IntegerField(blank=True,null=True)
    dob = models.DateField(blank=True,null=True)
    age = models.PositiveIntegerField(blank=True,null=True)

    advisor = models.ForeignKey('Staff',blank=True,on_delete=models.DO_NOTHING,related_name='Advisor',null=True)
    mentor = models.ForeignKey('Staff',blank=True,on_delete=models.DO_NOTHING,related_name='Mentor',null=True)
    hod = models.ForeignKey('Staff',blank=True,on_delete=models.DO_NOTHING,related_name='HOD',null=True)
    
    teaching_staffs = models.ManyToManyField('Staff',blank=True)
    feedback_for = models.ManyToManyField('IndividualStaffRating',related_name='for_staff_rating',blank=True)
    feedback_history = models.ManyToManyField('IndividualStaffRating',related_name='for_staff_rating_history',blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def __str__(self) -> str:
        return f"{self.user.username} {self.department}-{self.year}"

    def feedback_clear(self):
        self.feedback_for.clear()
        return True


class Staff(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='staff')
    name = models.CharField(max_length=50,blank=True,null=True)
    profile = models.ImageField(upload_to='profiles',blank=True)
    
    department = models.PositiveIntegerField(choices=SDEPT,default=0,null=True)
    address = models.TextField(blank=True,null=True)
    mobile = models.IntegerField(blank=True,null=True)
    dob = models.DateField(blank=True,null=True)
    age = models.PositiveIntegerField(blank=True,null=True)

    position = models.PositiveIntegerField(choices=POS,default=0)

    my_feedbacks = models.ManyToManyField('IndividualStaffRating',related_name='my_ratings',blank=True)

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def __str__(self) -> str:
        return f"{self.name} {self.user.username} {SDEPT[self.department][1]}"


class HOD(models.Model):
    user = models.ForeignKey('Staff',on_delete=models.CASCADE)
    
    get_feedback = models.BooleanField(default=False)
    get_spot_feedback = models.BooleanField(default=False)
    department = models.PositiveIntegerField(choices=SDEPT,default=2,null=True)
    staffs = models.ManyToManyField('Staff',related_name='my_staffs',blank=True)
    students = models.ManyToManyField('Student',related_name='students',blank=True)
    assign_feedback = models.ManyToManyField('Staff',related_name='assign_feed',blank=True)

    spot_feedback = models.ManyToManyField('SpotFeedback',blank=True)

    def __str__(self) -> str:
        return f" {self.user.name} - {self.user.department}"

class OD(models.Model):
    user = models.ForeignKey(Student,on_delete=models.CASCADE,related_name='s_student')

    sub = models.CharField(max_length=150)
    body = models.TextField()

    start = models.DateTimeField(verbose_name="From-Date")
    end = models.DateTimeField(verbose_name="To-Date")

    proof = models.FileField(upload_to='od/proof',blank=True)
    certificate = models.FileField(upload_to='od/proof/certificate',blank=True)

    # Status
    Astatus = models.CharField(choices=STATUS,max_length=50,default="Pending")
    Mstatus = models.CharField(choices=STATUS,max_length=50,default="Pending")
    Hstatus = models.CharField(choices=STATUS,max_length=50,default="Pending")

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def __str__(self) -> str:
        return f"{self.user.name} {self.sub}"



class LEAVE(models.Model):

    user = models.ForeignKey(Student,on_delete=models.CASCADE,related_name='sl_student')

    sub = models.CharField(max_length=150)
    body = models.TextField()

    start = models.DateTimeField(verbose_name="From-Date")
    end = models.DateTimeField(verbose_name="To-Date")

    proof = models.FileField(upload_to='leave/proof',blank=True)
    certificate = models.FileField(upload_to='leave/proof/certificate',blank=True)

    # Status
    Astatus = models.CharField(choices=STATUS,max_length=50,default="Pending")
    Mstatus = models.CharField(choices=STATUS,max_length=50,default="Pending")
    Hstatus = models.CharField(choices=STATUS,max_length=50,default="Pending")

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def __str__(self) -> str:
        return f"{self.user.name} {self.sub}"
    


class GATEPASS(models.Model):
    user = models.ForeignKey(Student,on_delete=models.CASCADE,related_name='sg_student')

    sub = models.CharField(max_length=150)

    start = models.DateTimeField(verbose_name="From-Date")
    end = models.DateTimeField(verbose_name="To-Date")

    # Status
    Astatus = models.CharField(choices=STATUS,max_length=50,default="Pending")
    Mstatus = models.CharField(choices=STATUS,max_length=50,default="Pending")
    Hstatus = models.CharField(choices=STATUS,max_length=50,default="Pending")

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def __str__(self) -> str:
        return f"{self.user.name} {self.sub}"

class RatingQuestions(models.Model):
    user = models.ForeignKey(HOD,on_delete=models.CASCADE)
    ques = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
    def __str__(self):
        return f"{self.ques}"
    

class StaffRating(models.Model):
    staff = models.ForeignKey(Staff,on_delete=models.CASCADE)
    student = models.ForeignKey(Student,on_delete=models.CASCADE)
    ques = models.ForeignKey(RatingQuestions,null=True,blank=True,on_delete=models.CASCADE)
    points = models.PositiveIntegerField(default=0)
    comments = models.CharField(max_length=100,default="Nill")
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-id']
    
    def __str__(self):
        return f"{self.staff.name} - {str(self.points)}"
    
    

class IndividualStaffRating(models.Model):
    staff = models.ForeignKey('Staff',on_delete=models.CASCADE)
    student = models.ForeignKey(Student,on_delete=models.CASCADE)
    ratings = models.ManyToManyField('StaffRating',related_name='StaffRating_Individual',blank=True)
    is_feedbacked = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-id']
    
    def __str__(self):
        return f"{self.staff.name} - {self.avg()}"
    
    def avg(self):
        avg = 0.0
        inr = self.ratings.all()
        if len(inr)==0:
            return 0
        for i in  inr:
            avg += i.points

        return round(float(avg/len(inr)))


class SpotFeedback(models.Model):
    user = models.ForeignKey('Staff',on_delete = models.CASCADE,related_name='hod_spot')
    staff = models.ForeignKey('Staff',on_delete = models.CASCADE,related_name='staff_spot')
    year = models.PositiveIntegerField(choices=YEAR,default=1,null=True)
    section = models.PositiveIntegerField(choices=SECTION,default=2)
    
    feebacks = models.ManyToManyField('IndividualStaffRating',blank=True)
    is_open = models.BooleanField(default=False)
    students = models.ManyToManyField('Student',blank=True)
    completed_students = models.ManyToManyField('Student',blank=True,related_name='c_std')
    created = models.DateTimeField(auto_now_add=True)
    
    qr_code = models.ImageField(upload_to='Spot/qrcodes/',blank=True)
    
    url = models.URLField(max_length=200,blank=True)
    
    def __str__(self):
        return f"{self.staff.name} - {self.avg()}"
    
    def avg(self):
        avg = 0.0
        inr = self.feebacks.all()
        if len(inr)==0:
            return 0
        for i in  inr:
            avg += i.avg()

        return round(float(avg/len(inr)))
    
    def get_cls(self):
        return [SECTION[self.section],YEAR[self.year-1]]
    
    def get_absolute_url(self):
        return reverse('student_feedback_form', args=[str(self.staff.id),'spf'])
