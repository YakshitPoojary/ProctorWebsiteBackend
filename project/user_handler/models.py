from .tokens import CustomRefreshToken
from django.db import models
from rest_framework_simplejwt.tokens import RefreshToken

class Branch(models.Model):
    branch_name = models.CharField(max_length=300,unique=True)
    branch_abbreviation = models.CharField(max_length=20,primary_key=True,unique=True)

class Faculty(models.Model):
    dept = models.CharField(max_length=100)
    employee_code = models.PositiveIntegerField(unique=True)
    faculty_abbreviation = models.CharField(max_length=20, primary_key=True,unique=True)
    faculty_name = models.CharField(max_length=255)
    faculty_email = models.EmailField(max_length=255)
    experience = models.CharField(max_length=255)
    post = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=10)
    
class Staff(models.Model):

    dept = models.CharField(max_length=100)
    employee_code = models.PositiveIntegerField(unique=True)
    staff_abbreviation = models.CharField(max_length=20, primary_key=True, unique=True)
    staff_name = models.CharField(max_length=255)
    staff_email = models.EmailField(verbose_name='email address', max_length=255,unique=True)
    experience = models.CharField(max_length=255)
    post = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=10)

class Student(models.Model):

    primary_field = models.CharField(max_length=255, primary_key=True)
    student_branch = models.CharField(max_length=100)
    student_name = models.CharField(max_length=100)
    roll_number = models.PositiveBigIntegerField()
    email = models.EmailField(max_length=255)
    proctor_abbreviation = models.CharField(max_length=10)
    student_contact_no = models.CharField(max_length=20)
    parents_contact_no = models.CharField(max_length=20, blank=True, null=True)
    parent_email_id = models.EmailField(max_length=100, blank=True, null=True)
    year = models.CharField(max_length=20)
    session = models.CharField(max_length=20)
    current_year = models.CharField(max_length=20)
    division = models.CharField(max_length=255)
    course_1 = models.CharField(max_length=100, default='null', blank=True, null=True)
    course_2 = models.CharField(max_length=100, default='null', blank=True, null=True)
    course_3 = models.CharField(max_length=100, default='null', blank=True, null=True)
    course_4 = models.CharField(max_length=100, default='null', blank=True, null=True)
    course_5 = models.CharField(max_length=100, default='null', blank=True, null=True)
    course_6 = models.CharField(max_length=100, default='null', blank=True, null=True)
    course_7 = models.CharField(max_length=100, default='null', blank=True, null=True)
    course_8 = models.CharField(max_length=100, default='null', blank=True, null=True)
    course_9 = models.CharField(max_length=100, default='null', blank=True, null=True)
    course_10 = models.CharField(max_length=100, default='null', blank=True, null=True)
    course_11 = models.CharField(max_length=100, default='null',blank=True, null=True)
    course_12 = models.CharField(max_length=100, default='null', blank=True, null=True)
    course_13 = models.CharField(max_length=100, default='null', blank=True, null=True)
    course_14 = models.CharField(max_length=100, default='null', blank=True, null=True)
    course_15 = models.CharField(max_length=100, default='null', blank=True, null=True)

class Course(models.Model):
    branch = models.CharField(max_length=100)
    course_code = models.CharField(max_length=20, primary_key=True, unique=True)
    course_abbreviation = models.CharField(max_length=10, unique=True)
    course_name = models.CharField(max_length=200, unique=True)
    sem = models.IntegerField()
    scheme_name = models.CharField(max_length=100)
    credit = models.IntegerField()
    hours = models.IntegerField()
    tutorial = models.CharField(max_length=100)

class CourseAllotment(models.Model):
    faculty_abbreviation = models.CharField(max_length=20)
    course_code = models.CharField(max_length=20)
    course_name = models.CharField(max_length=255)
    year = models.CharField(max_length=20)
    session = models.CharField(max_length=10)
    course_abbreviation = models.CharField(max_length=100)
    staff_abbreviation = models.CharField(max_length=20)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['year', 'session', 'course_code'], name='unique-course-allotment')
        ]
    
class StudentAchievement(models.Model):
    id = models.AutoField(primary_key=True)
    roll_number = models.PositiveBigIntegerField()
    activity_type = models.CharField(max_length=100)
    activity_members = models.CharField(max_length=100, null=True, blank=True)
    group_members = models.JSONField(null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    upload_file = models.FileField(upload_to='media/')
    approved = models.CharField(max_length=1)
    proctor = models.CharField(max_length=10)

class StudentInternship(models.Model):
    id = models.AutoField(primary_key=True)
    roll_number = models.PositiveBigIntegerField()
    company_name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    company_email = models.CharField(max_length=100)
    company_phone = models.CharField(max_length=100)
    company_website = models.CharField(max_length=100)
    supervisor = models.CharField(max_length=100)
    hours = models.CharField(max_length=100)
    job_role = models.CharField(max_length=100)
    description = models.TextField(blank=True,null=True)
    upload_file = models.FileField(upload_to='media/')
    approved = models.CharField(max_length=1)
    proctor = models.CharField(max_length=10)

class AdminCredentials(models.Model):
    admin_email = models.EmailField(verbose_name='email address', max_length=255,unique=True)
    admin_password = models.CharField(max_length=255)

class SubAdminCredentials(models.Model):
    id = models.AutoField(primary_key=True)
    sub_admin_email = models.EmailField(verbose_name='email address', max_length=255,unique=True, blank=True, null=True)
    sub_admin_password = models.CharField(max_length=255)
    branch = models.CharField(max_length=20, default='None')

class AcademicYear(models.Model):
    year = models.CharField(max_length=20)
    session = models.CharField(max_length=20)
    
class Marks(models.Model):

    year = models.CharField(max_length=20)
    session = models.CharField(max_length=20)
    branch = models.CharField(max_length=100)
    course_code = models.CharField(max_length=20)
    division = models.CharField(max_length=100)
    student_name = models.CharField(max_length=100)
    roll_number = models.PositiveBigIntegerField()
    ise = models.PositiveBigIntegerField(blank=True, null=True)
    ia1 = models.PositiveBigIntegerField(blank=True, null=True)
    ia2 = models.PositiveBigIntegerField(blank=True, null=True)
    ia3 = models.PositiveBigIntegerField(blank=True, null=True)
    ca = models.PositiveBigIntegerField(blank=True, null=True)
    ese = models.PositiveBigIntegerField(blank=True, null=True)
    tw = models.PositiveBigIntegerField(blank=True, null=True)
    oral=models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['course_code', 'roll_number'], name='unique_marks_course_roll')
        ]

class Attendance(models.Model):
    year = models.CharField(max_length=20)
    session = models.CharField(max_length=20)
    branch = models.CharField(max_length=100)
    course_code = models.CharField(max_length=20)
    class_type = models.CharField(max_length=100)
    student_name = models.CharField(max_length=100)
    roll_number = models.PositiveBigIntegerField()
    january = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    february = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    march = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    april = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    may = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    june = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    july = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    august = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    september = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    october = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    november = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    december = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['course_code', 'roll_number', 'class_type'], name='unique_attendance_course_roll')
        ]

class UserCredentials(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True, blank=True, null=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, unique=True)

    def get_tokens(self):
        refresh = CustomRefreshToken.for_user(self)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

