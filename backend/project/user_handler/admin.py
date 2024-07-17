from django.contrib import admin

from .models import Branch, Faculty, Staff, Student, Course, CourseAllotment, StudentAchievement, StudentInternship, AdminCredentials, SubAdminCredentials, AcademicYear, Marks, Attendance, UserCredentials

class BranchAdmin(admin.ModelAdmin):
    list_display = ['branch_name','branch_abbreviation']

class FacultyAdmin(admin.ModelAdmin):
    list_display = [
        'dept', 'employee_code', 'faculty_abbreviation', 'faculty_name', 'faculty_email',
        'experience', 'post', 'mobile_number', 'display_courses_taught'
    ]

    def display_courses_taught(self, obj):
        courses_taught = CourseAllotment.objects.filter(faculty_abbreviation=obj.faculty_abbreviation)
        return ', '.join([f"{course.course_code} - {course.course_name}" for course in courses_taught])
    

    display_courses_taught.short_description = 'Courses Taught'

class StaffAdmin(admin.ModelAdmin):
    list_display = [
        'dept', 'employee_code', 'staff_abbreviation', 'staff_name', 'staff_email',
        'experience', 'post', 'mobile_number'
    ]


class StudentAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Student._meta.get_fields()]

class CourseAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Course._meta.get_fields()]

class CourseAllotmentAdmin(admin.ModelAdmin):
    list_display = [field.name for field in CourseAllotment._meta.get_fields()]

class StudentAchievementAdmin(admin.ModelAdmin):
    list_display = [field.name for field in StudentAchievement._meta.get_fields()]

class StudentInternshipAdmin(admin.ModelAdmin):
    list_display = [field.name for field in StudentInternship._meta.get_fields()]

class AdminCredentialsAdmin(admin.ModelAdmin):
    list_display = [field.name for field in AdminCredentials._meta.get_fields()]

class SubAdminCredentialsAdmin(admin.ModelAdmin):
    list_display = [field.name for field in SubAdminCredentials._meta.get_fields()]

class AcademicYearAdmin(admin.ModelAdmin):
    list_display = [field.name for field in AcademicYear._meta.get_fields()]

class MarksAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Marks._meta.get_fields()]

class AttendanceAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Attendance._meta.get_fields()]

class UserCredentialsAdmin(admin.ModelAdmin):
    list_display = [field.name for field in UserCredentials._meta.get_fields()]


admin.site.register(Branch,BranchAdmin)
admin.site.register(Faculty,FacultyAdmin)
admin.site.register(Staff,StaffAdmin)
admin.site.register(Student,StudentAdmin)
admin.site.register(Course,CourseAdmin)
admin.site.register(CourseAllotment,CourseAllotmentAdmin)
admin.site.register(StudentAchievement,StudentAchievementAdmin)
admin.site.register(StudentInternship,StudentInternshipAdmin)
admin.site.register(AdminCredentials,AdminCredentialsAdmin)
admin.site.register(SubAdminCredentials,SubAdminCredentialsAdmin)
admin.site.register(AcademicYear,AcademicYearAdmin)
admin.site.register(Marks,MarksAdmin)
admin.site.register(Attendance,AttendanceAdmin)
admin.site.register(UserCredentials,UserCredentialsAdmin)