from django.urls import path, include
from user_handler import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('branch', views.BranchViewSet, basename='branch')
router.register('faculty', views.FacultyViewSet, basename='faculty')
router.register('staff', views.StaffViewSet, basename='staff')
router.register('student', views.StudentViewSet, basename='student')
router.register('course', views.CourseViewSet, basename='course')
router.register('courseallotment', views.CourseAllotmentViewSet, basename='courseallotment')
router.register('marks', views.MarksViewSet, basename='marks')
router.register('attendance', views.AttendanceViewSet, basename='attendance')
router.register('studentachievement', views.StudentAchievementViewSet, basename='studentachievement')
router.register('studentinternship', views.StudentInternshipViewSet, basename='studentinternship')
router.register('academicyear', views.AcademicYearViewSet, basename='academicyear')
router.register('subadmincredentials', views.SubadminViewSet, basename='subadmincredentials')
router.register('admincredentials', views.AdminViewSet, basename='admincredentials')



urlpatterns = [
    path('', include(router.urls)),
    
    # Check Password before deleting anything
    path('check/', views.UserCredentialsViewSet.as_view({'get': 'check'}), name='check-password-before-delete'),
    # Delete Academic Year Session
    path('academicyear/<str:year>/<str:session>/delete/', views.AcademicYearViewSet.as_view({'delete':'destroy'}), name='delete-session'),
    # Search student for subadmin and admin
    path('search/student/', views.StudentViewSet.as_view({'get': 'search'}), name='search-student'),


    #! Download csv format
    path('download-csv/<str:model>/', views.DownloadCSV.as_view(), name='download-csv'),

    #! Authentication and Logout
    path('api/login/', views.UserLogin.as_view(), name='login'),
    path('api/logout/', views.UserLogout.as_view(), name='logout'),
    # Forgot Password
    path('change/password/', views.ChangePassword.as_view({'post': 'post'}), name='change'),
    path('verify/otp/', views.ChangePassword.as_view({'post': 'verify_otp'}), name='verify_otp'),
    path('reset/password/', views.ChangePassword.as_view({'post': 'reset_password'}), name='reset_password'),

    #! Admin
    # Check Password before deleting anything
    path('admincredentials/check/<str:password>/', views.AdminViewSet.as_view({'get': 'check'}), name='check-admin'),
    # Delete Branch (not sure if admin should)
    path('branch/<str:branch_abbreviation>/delete/', views.BranchViewSet.as_view({'delete':'destroy'}), name='delete-branch'),
    # Display Branch subadmin details
    path('subadmincredentials/list/<str:branch>/', views.SubadminViewSet.as_view({'get': 'list'}), name='get-subadmin-credentials'),
    # Delete subadmin details
    path('subadmincredentials/<str:sub_admin_username>/delete/', views.SubadminViewSet.as_view({'delete': 'destroy'}), name='delete-subadmin-credentials'),


    #! Subadmin
    # Retreive subadmin info after login
    path('subadmincredentials/details/<str:sub_admin_email>/', views.SubadminViewSet.as_view({'get': 'retrieve'}), name='get-subadmin-credentials'),
    # List faculty based on branch
    path('faculty/branch/<str:branch>/', views.FacultyViewSet.as_view({'get': 'list'}), name='get-branch-faculty'),
    # List branches based on branch
    path('course/list/<str:branch>/', views.CourseViewSet.as_view({'get': 'list'}), name='course-list-by-branch'),
    # List staff based on branch
    path('staff/list/<str:branch>/', views.StaffViewSet.as_view({'get': 'list'}), name='staff-list-by-branch'),
    # List students based on branch and current Year
    path('students/<str:year>/<str:session>/<str:branch>/', views.StudentViewSet.as_view({'get': 'list'}), name='student-by-year-session-branch'),
    # List course allotments
    path('courseallotment/<str:year>/<str:session>/<str:branch>/', views.CourseAllotmentViewSet.as_view({'get': 'list'}), name='get-course-allotment-list'),
    # Edit faculty details
    path('subadmin/faculty/edit', views.FacultyViewSet.as_view({'post': 'edit'}), name='edit_faculty'),
    # Edit course details
    path('subadmin/course/edit', views.CourseViewSet.as_view({'post': 'edit'}), name='edit_course'),
    # Edit student details
    path('subadmin/student/edit', views.StudentViewSet.as_view({'post': 'edit'}), name='edit_student'),
    # Edit staff details
    path('subadmin/staff/edit', views.StaffViewSet.as_view({'post': 'edit'}), name='edit_staff'),
    # Delete course allotment
    path('courseallotment/<str:faculty_abbreviation>/<str:course_code>/', views.CourseAllotmentViewSet.as_view({'delete': 'destroy'}), name='delete-course-allotment'),

    #! Faculty
    # Retrive Faculty info after login
    path('faculty/details/<str:faculty_email>/', views.FacultyViewSet.as_view({'get': 'retrieve'}), name='get-faculty-credentials'),
    # List course allotments for faculty and staff
    path('courseallotment/abbr/<str:abbreviation>/<str:year>/<str:session>', views.CourseAllotmentViewSet.as_view({'get': 'list2'}), name='get-course-allotment-faculty'),
    # List proctees
    path('student/proctor/<str:proctor_abbreviation>/', views.FacultyViewSet.as_view({'get': 'proctees'}), name='proctees'),
    # List unapproved achievements and internships of proctees
    path('studentachievement/unapproved/<str:proctor>/', views.StudentAchievementViewSet.as_view({'get': 'unapproved'}), name='student-achievement'),
    path('studentinternship/unapproved/<str:proctor>/', views.StudentInternshipViewSet.as_view({'get': 'unapproved'}), name='student-internship'),
    #Approve achievements and internships
    path('studentachievement/approve/<int:achievement_id>/',views.StudentAchievementViewSet.as_view({'post':'approve'}), name='student-achievement-approval'),
    path('studentinternship/approve/<int:internship_id>/',views.StudentInternshipViewSet.as_view({'post':'approve'}), name='student-internship-approval'),
    # Reject and delete achievements and internships of proctees
    path('studentachievement/reject/<int:achievement_id>/',views.StudentAchievementViewSet.as_view({'post':'reject'}), name='student-achievement-approval'),
    path('studentinternship/reject/<int:internship_id>/',views.StudentInternshipViewSet.as_view({'post':'reject'}), name='student-internship-approval'),



    #! Student
    # Retrive Student info after login
    path('student/recent/<str:student_email>/', views.StudentViewSet.as_view({'get': 'recent'}), name='student-by-proctor-abbreviation'),
    # List Student available sessions for marks
    path('marks/<int:roll_number>', views.MarksViewSet.as_view({'get': 'list2'}), name='marks-list-student'),
    # List Student marks based on year session
    path('marks/<str:year>/<str:session>/<int:roll_number>/', views.MarksViewSet.as_view({'get': 'list'}), name='marks-list-student'),
    # List achievements of student
    path('studentachievement/list/<str:roll_number>/', views.StudentAchievementViewSet.as_view({'get': 'list'}), name='student-achievement'),
    path('studentinternship/list/<str:roll_number>/', views.StudentInternshipViewSet.as_view({'get': 'list'}), name='student-internship'),
    # Delete achievement (only for student)
    path('studentachievement/delete/<int:pk>/', views.StudentAchievementViewSet.as_view({'delete': 'destroy'}), name='student-achievement-delete'),
    path('studentinternship/delete/<int:pk>/', views.StudentInternshipViewSet.as_view({'delete': 'destroy'}), name='student-internship-delete'),


    #! Staff
    # Retrive staff info after login
    path('staff/details/<str:staff_email>/', views.StaffViewSet.as_view({'get': 'retrieve'}), name='get-staff-credentials'),
    # Get attendence excel format on year,session,code
    path('attendance/<str:course_code>/<str:year>/<str:session>/download-csv/', views.DownloadAllMonthAttendanceCSV.as_view(), name='download-all-month-attendance-csv'),
    # List attendance based on year,session, code
    path('attendance/<str:course_code>/<str:year>/<str:session>/list/', views.AttendanceViewSet.as_view({'get': 'list'}), name='list-course-year-session-attendance'),
    path('course/<str:course_code>/', views.CourseViewSet.as_view({'get':'get_course_details'}), name='get-course-details'),


    # path('courseallotment/<str:year>/<str:session>/', views.CourseAllotmentViewSet.as_view({'get': 'list3'}), name='get-course-allotment-year-session'),
    # path('courseallotment/staff/<str:staff_abbreviation>/', views.CourseAllotmentViewSet.as_view({'get': 'list3'}), name='get-course-allotment-staff'),

    path('marks/<str:exam>/<str:course_code>/<int:roll_number>/delete/', views.MarksViewSet.as_view({'delete': 'delete_exam_marks'}), name='marks-delete-exam'),
    path('marks/<str:exam>/<str:course_code>/download-csv/', views.DownloadExamCSV.as_view(), name='download-exam-csv'),
    path('marks/<str:course_code>/<str:year>/<str:session>/download-csv/', views.DownloadAllExamCSV.as_view(), name='download-all-exam-csv'),
    path('marks/<str:course_code>/<int:roll_number>/', views.MarksViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}), name='marks-retrieve-delete'),
    path('marks/<str:year>/<str:session>/<str:course_code>', views.MarksViewSet.as_view({'get': 'list'}), name='marks-list'),
    path('marks/<str:year>/<str:session>', views.MarksViewSet.as_view({'get': 'list'}), name='marks-list-session'),

    

    
    path('attendance/<str:month>/<str:course_code>/<int:roll_number>/delete/', views.AttendanceViewSet.as_view({'delete': 'delete_month_attendance'}), name='attendance-delete-month'),
    path('attendance/<str:month>/<str:course_code>/download-csv/', views.DownloadMonthAttendanceCSV.as_view(), name='download-month-attendance-csv'),
    path('attendance/<str:course_code>/<int:roll_number>/', views.AttendanceViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}), name='attendance-retrieve-delete'),
    path('attendance/student/<str:course_code>/<int:roll_number>/', views.AttendanceViewSet.as_view({'get': 'get_student_attendance'}), name='attendance-get_student_attendance'),    
    

    # path('studentachievement/', views.StudentAchievementViewSet.as_view({'post': 'create'}), name='student-achievement'),




    path('api/user/', views.UserDetailView.as_view(), name='user-detail'),

    path('student/marks/<int:roll_number>/', views.MarksViewSet.as_view({'get': 'retrieve'}), name='student-marks'),

    # path('studentachievements/<int:pk>/', views.UpdateAchievementApproval.as_view()),
]