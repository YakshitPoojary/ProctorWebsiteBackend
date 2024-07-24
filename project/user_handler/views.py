from io import TextIOWrapper
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.response import Response
import csv
from rest_framework import generics
from rest_framework.views import APIView
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from datetime import datetime
from django.db import transaction
import re
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.hashers import make_password, check_password
from . import models, serializers  
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Max
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
import random

class UserCredentialsViewSet(viewsets.ViewSet):
    def check(self, request):
        try:
            username = request.query_params.get('username')          
            password = request.query_params.get('password')
            user = models.UserCredentials.objects.get(username=username)            
            if check_password(password, user.password):
                return Response(True, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Incorrect password'}, status=status.HTTP_400_BAD_REQUEST)
        except models.AdminCredentials.DoesNotExist:
            return Response({'error': 'Incorrect email or password'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminViewSet(viewsets.ViewSet):

    def create(self, request):
        try:
            email = request.data.get('email').strip()
            password = request.data.get('password')

            if not email or not password:
                return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)
            username = email.split('@')[0]

            hashed_password = make_password(password)
            admin_instance = models.AdminCredentials(admin_email=email, admin_password=hashed_password)
            admin_instance.save()
            user_instance = models.UserCredentials(email=email, password=hashed_password, role='admin', username=username)
            user_instance.save()
            serializer = serializers.AdminCredentialsSerializer(admin_instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SubadminViewSet(viewsets.ViewSet):
    def check(self, request, password=None):
        try:
            admin_instance = models.UserCredentials.objects.get(role='admin')            
            if check_password(password, admin_instance.password):
                serializer = serializers.AdminCredentialsSerializer(admin_instance)
                return Response(True, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Incorrect password'}, status=status.HTTP_400_BAD_REQUEST)
        except models.AdminCredentials.DoesNotExist:
            return Response({'error': 'Incorrect email or password'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list(self, request, branch=None):
        if branch is None:
            return Response({"message": "Branch parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        subadmin_instances = models.SubAdminCredentials.objects.filter(branch=branch)
        if not subadmin_instances:
            return Response({"message": "Subadmin record not found."}, status=status.HTTP_404_NOT_FOUND)
    
        serializer = serializers.SubAdminCredentialsSerializer(subadmin_instances, many=True)
        return Response(serializer.data)

    def retrieve(self, request, sub_admin_email=None):
        try:
            subadmin_instance = models.SubAdminCredentials.objects.get(sub_admin_email=sub_admin_email)
            serializer = serializers.SubAdminCredentialsSerializer(subadmin_instance)
            return Response(serializer.data)
        except models.SubAdminCredentials.DoesNotExist:
            return Response({"message": "Subadmin not found."}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, sub_admin_email):
        try:
            subadmin_instance = models.SubAdminCredentials.objects.get(sub_admin_email=sub_admin_email)
            email = serializers.FacultySerializer(faculty_instance).data.get('sub_admin_email')
            user_instance = models.UserCredentials.objects.get(email=email)
            user_instance.delete()
            subadmin_instance.delete()
            return Response({"message": 'Subadmin deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
        except models.SubAdminCredentials.DoesNotExist:
            return Response({"message": "Subadmin not found."}, status=status.HTTP_404_NOT_FOUND)
    
class BranchViewSet(viewsets.ViewSet):
    def list(self,request):
        years=models.Branch.objects.all()
        serializer = serializers.BranchSerializer(years, many=True)
        return Response(serializer.data)

    def create(self, request):
        branch_name = request.data.get('branch_name').upper().strip()
        branch_abbreviation = request.data.get('branch_abbreviation').upper().strip()
        sub_admin_email = request.data.get('subadmin_email').lower().strip()
        sub_admin_username = request.data.get('subadmin_username').strip()
        sub_admin_password = request.data.get('subadmin_password').strip()
        hashed_password = make_password(sub_admin_password)

        if not branch_name:
            return Response({'error': 'Name is required.'}, status=status.HTTP_400_BAD_REQUEST)
        elif not branch_abbreviation:
            return Response({'error': 'Abbreviation is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if models.Branch.objects.filter(branch_name=branch_name).exists():
            return Response({'error': 'Branch name already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        if models.Branch.objects.filter(branch_abbreviation=branch_abbreviation).exists():
            return Response({'error': 'Branch abbreviation already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        if models.SubAdminCredentials.objects.filter(sub_admin_email=sub_admin_email).exists():
            return Response({'error': 'Sub-admin email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        if models.UserCredentials.objects.filter(email=sub_admin_email).exists():
            return Response({'error': 'User email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        if models.UserCredentials.objects.filter(username=sub_admin_username).exists():
            return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = serializers.BranchSerializer(data={
            'branch_name': branch_name,
            'branch_abbreviation': branch_abbreviation,
        })

        serializer2 = serializers.SubAdminCredentialsSerializer(data={
            'sub_admin_email': sub_admin_email,
            'sub_admin_password': hashed_password,
            'branch': branch_abbreviation,
        })

        serializer3 = serializers.UserCredentialsSerializer(data={
            'email': sub_admin_email,
            'password': hashed_password,
            'role': "subadmin",
            'username': sub_admin_username,
        })

        if serializer3.is_valid():
            serializer3.save()
        
        if serializer2.is_valid():
            serializer2.save()
        
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Branch added to Branch models successfully."}, status=status.HTTP_201_CREATED)
        
        return Response({'error': 'Invalid data provided.'}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, branch_abbreviation=None):
        try:
            branch_instance = models.Branch.objects.get(branch_abbreviation=branch_abbreviation)
            branch_instance.delete()
            return Response({"message": "Branch data deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except models.Marks.DoesNotExist:
            return Response({"message": "Branch data not found."}, status=status.HTTP_404_NOT_FOUND)

class FacultyViewSet(viewsets.ViewSet):
    def edit(self, request):
        faculty_abbreviation = request.data.get('faculty_abbreviation')
        try:
            faculty_instance = models.Faculty.objects.get(faculty_abbreviation=faculty_abbreviation)
            
            faculty_instance.dept = request.data.get('dept', faculty_instance.dept)
            faculty_instance.faculty_name = request.data.get('faculty_name', faculty_instance.faculty_name)
            faculty_instance.mobile_number = request.data.get('mobile_number', faculty_instance.mobile_number)
            faculty_instance.post = request.data.get('post', faculty_instance.post)
            faculty_instance.experience = request.data.get('experience', faculty_instance.experience)
            
            faculty_instance.save()
            
            serializer = serializers.FacultySerializer(faculty_instance)
            return Response(serializer.data)
        except models.Faculty.DoesNotExist:
            return Response({"error": "Faculty not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, branch=None):
        if branch:
            faculties = models.Faculty.objects.all().filter(dept=branch).order_by('faculty_name')
            serializer = serializers.FacultySerializer(faculties, many=True)
        return Response(serializer.data)

    def proctees(self,request, proctor_abbreviation):
        proctees = models.Student.objects.filter(proctor_abbreviation=proctor_abbreviation)
        serializer = serializers.StudentSerializer(proctees, many=True)
        return Response(serializer.data)

    def retrieve(self, request, faculty_email=None):
        try:
            faculty_instance = models.Faculty.objects.get(faculty_email=faculty_email)
            serializer = serializers.FacultySerializer(faculty_instance)
            return Response(serializer.data)
        except models.Faculty.DoesNotExist:
            return Response({"message": "Faculty not found."}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"message": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)
        
        csv_data = csv.reader(TextIOWrapper(file, encoding='utf-8'))
        next(csv_data, None)

        validate = lambda x: x.strip().upper()
        error_messages = set()
        
        with transaction.atomic():
            for row in csv_data:
                for i, entry in enumerate(row):
                    row[i] = validate(entry)

                dept = row[0]
                employee_code = row[1]
                faculty_abbreviation = row[2]
                faculty_name = row[3]
                faculty_email = row[4].lower()
                experience = row[5]
                post = row[6]
                mobile_number = row[7]
                
                if not employee_code.isdigit():
                    error_messages.add(f"Invalid employee code: {row[1]}")
                    continue
                employee_code = int(employee_code)

                if not re.match(r'^[a-zA-Z0-9._%+-]+@somaiya.edu$', faculty_email):
                    error_messages.add(f"{faculty_abbreviation}'s email {faculty_email} is invalid.")
                    continue
                
                branch = models.Branch.objects.filter(branch_abbreviation=dept)
                if not branch:
                    error_messages.add(f"{dept} doesn't exist")
                    continue
                
                if len(mobile_number) != 10 or not mobile_number.isdigit():
                    error_messages.add(f"{faculty_abbreviation}'s mobile number {mobile_number} is invalid")
                    continue
                
                try:
                    faculty_instance = models.Faculty.objects.get(employee_code=employee_code)
                    if faculty_instance.faculty_abbreviation.upper() != faculty_abbreviation:
                        error_messages.add(f"This employee code exists: {employee_code}")
                        continue
                except models.Faculty.DoesNotExist:
                    faculty_instance = None

                if faculty_instance:
                    serializer = serializers.FacultySerializer(faculty_instance, data={
                        'dept': dept,
                        'faculty_name': faculty_name,
                        'faculty_email': faculty_email,
                        'experience': experience,
                        'post': post,
                        'mobile_number': mobile_number,
                    }, partial=True)
                else:
                    serializer = serializers.FacultySerializer(data={
                        'dept': dept,
                        'employee_code': employee_code,
                        'faculty_abbreviation': faculty_abbreviation,
                        'faculty_name': faculty_name,
                        'faculty_email': faculty_email,
                        'experience': experience,
                        'post': post,
                        'mobile_number': mobile_number,
                    })

                if serializer.is_valid():
                    serializer.save()
                    
                    if not faculty_instance:
                        hashed_password = make_password(str(employee_code))
                        username = faculty_email.split('@')[0]
                        serializer3 = serializers.UserCredentialsSerializer(data={
                            'email': faculty_email,
                            'password': hashed_password,
                            'role': "faculty",
                            'username': username,
                        })

                        if serializer3.is_valid():
                            serializer3.save()
                    
        if error_messages:
            return Response({
                "message": "Error adding CSV data.",
                "errors": error_messages,
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "CSV data added to faculty models successfully."}, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        try:
            faculty_instance = models.Faculty.objects.get(pk=pk)
            email = serializers.FacultySerializer(faculty_instance).data.get('faculty_email')
            user_instance = models.UserCredentials.objects.get(email=email)
            user_instance.delete()
            faculty_instance.delete()
            return Response({"message": "Faculty deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except models.Faculty.DoesNotExist:
            return Response({"message": "Faculty not found."}, status=status.HTTP_404_NOT_FOUND)

class StaffViewSet(viewsets.ViewSet):
    def edit(self, request):
        staff_abbreviation = request.data.get('staff_abbreviation')
        try:
            staff_instance = models.Staff.objects.get(staff_abbreviation=staff_abbreviation)
            staff_instance.staff_name = request.data.get('staff_name', staff_instance.staff_name)
            staff_instance.dept = request.data.get('dept', staff_instance.dept)
            staff_instance.experience = request.data.get('experience', staff_instance.experience)
            staff_instance.post = request.data.get('post', staff_instance.post)
            staff_instance.mobile_number = request.data.get('mobile_number', staff_instance.mobile_number)
            
            staff_instance.save()
            
            serializer = serializers.StaffSerializer(staff_instance)
            return Response(serializer.data)
        except models.Staff.DoesNotExist:
            return Response({"error": "Course not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, branch=None):
        if branch:
            staffs = models.Staff.objects.filter(dept=branch).order_by('staff_name')
        else:
            staffs = models.Staff.objects.all().order_by('staff_name')
        serializer = serializers.StaffSerializer(staffs, many=True)
        return Response(serializer.data)

    def retrieve(self, request, staff_email=None):
        try:
            staff_instance = models.Staff.objects.get(staff_email=staff_email)
            serializer = serializers.StaffSerializer(staff_instance)
            return Response(serializer.data)
        except models.Staff.DoesNotExist:
            return Response({"message": "Staff not found."}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"message": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)
        
        csv_data = csv.reader(TextIOWrapper(file, encoding='utf-8'))
        next(csv_data, None)
        
        validate = lambda x: x.strip().upper()
        error_messages = set()

        with transaction.atomic():
            for row in csv_data:
                for i, entry in enumerate(row):
                    row[i] = validate(entry)
                
                dept = row[0]
                employee_code = row[1]
                staff_abbreviation = row[2]
                staff_name = row[3]
                staff_email = row[4].lower()
                experience = row[5]
                post = row[6]
                mobile_number = row[7]

                if not employee_code.isdigit():
                    error_messages.add(f"Invalid employee code: {employee_code}")
                    continue
                employee_code = int(employee_code)

                if not re.match(r'^[a-zA-Z0-9._%+-]+@somaiya.edu$', staff_email):
                    error_messages.add(f"{staff_abbreviation}'s email {staff_email} is invalid.")
                    continue
                
                branch = models.Branch.objects.filter(branch_abbreviation=dept)
                if not branch:
                    error_messages.add(f"{dept} doesn't exist")
                    continue
                
                if len(mobile_number) != 10 or not mobile_number.isdigit():
                    error_messages.add(f"{staff_abbreviation}'s mobile number {mobile_number} is invalid")
                    continue
                
                try:
                    staff_instance = models.Staff.objects.get(employee_code=employee_code)
                    if staff_instance.staff_name.upper() != staff_name:
                        error_messages.add(f"This employee code exists: {employee_code}")
                        continue
                except models.Staff.DoesNotExist:
                    staff_instance = None

                if staff_instance:
                    serializer = serializers.StaffSerializer(staff_instance, data={
                        'dept': dept,
                        'employee_code': employee_code,
                        'staff_name': staff_name,
                        'staff_email': staff_email,
                        'experience': experience,
                        'post': post,
                        'mobile_number': mobile_number,
                    }, partial=True)
                else:
                    serializer = serializers.StaffSerializer(data={
                        'dept': dept,
                        'employee_code': employee_code,
                        'staff_abbreviation': staff_abbreviation,
                        'staff_name': staff_name,
                        'staff_email': staff_email,
                        'experience': experience,
                        'post': post,
                        'mobile_number': mobile_number,
                    })
                
                if serializer.is_valid():
                    serializer.save()
                    if not staff_instance:
                        hashed_password = make_password(str(employee_code))
                        username = staff_email.split('@')[0]
                        serializer3 = serializers.UserCredentialsSerializer(data={
                            'email': staff_email,
                            'password': hashed_password,
                            'role': "staff",
                            'username': username, 
                        })

                        if serializer3.is_valid():
                            serializer3.save()

        if error_messages:
            return Response({
                "message": "Error adding CSV data.",
                "errors": error_messages,
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "CSV data added to staff models successfully."}, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        try:
            staff_instance = models.Staff.objects.get(pk=pk)
            email = serializers.StaffSerializer(staff_instance).data.get('staff_email')
            user_instance = models.UserCredentials.objects.get(email=email)
            user_instance.delete()
            staff_instance.delete()
            return Response({"message": "Staff deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except models.Staff.DoesNotExist:
            return Response({"message": "Staff not found."}, status=status.HTTP_404_NOT_FOUND)

class StudentViewSet(viewsets.ViewSet):
    def edit(self, request):
        roll_number = request.data.get('roll_number')
        year = request.data.get('year')
        session = request.data.get('session')
        
        try:
            primary_field = f"{year}|{session}|{roll_number}".upper()
            student_instance = models.Student.objects.get(primary_field=primary_field)

            student_instance.student_name = request.data.get('student_name', student_instance.student_name)
            student_instance.student_contact_no = request.data.get('student_contact_no', student_instance.student_contact_no)
            student_instance.student_branch = request.data.get('student_branch', student_instance.student_branch)
            student_instance.email = request.data.get('email', student_instance.email)
            
            faculty = models.Faculty.objects.all()
            faculty = [faculty_object.faculty_abbreviation for faculty_object in faculty]
            proctor_abbreviation = request.data.get('proctor_abbreviation', student_instance.proctor_abbreviation)
            if proctor_abbreviation not in faculty:
                return Response({"error": f"Faculty of abbreviation {proctor_abbreviation} does not exist"}, status=status.HTTP_400_BAD_REQUEST)
            
            student_instance.proctor_abbreviation = proctor_abbreviation
            student_instance.save()

            serializer = serializers.StudentSerializer(student_instance)
            return Response(serializer.data)
        except models.Student.DoesNotExist:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def search(self, request):
        branch = request.query_params.get('branch')
        year_session = request.query_params.get('year')
        searchTerm = request.query_params.get('searchTerm')
        current_year = request.query_params.get('current_year', 'All')

        year, session = None, None

        if year_session:
            year, session = year_session.split('|')

        students = models.Student.objects.all()

        if branch:
            students = students.filter(student_branch=branch)
            print(branch)
            print("here 1")
        if year and session:
            students = students.filter(year=year, session=session)
            print("here 2")
        if current_year != 'All':
            students = students.filter(current_year=current_year)
            print(current_year)
            print("here 3")
        if searchTerm:
            if searchTerm.strip().isdigit():
                students = students.filter(roll_number__icontains=searchTerm)
            else:
                students = students.filter(student_name__icontains=searchTerm)
            print("here 3")
        
        if students.exists():
            recent_year = students.order_by('-year').first().year
            recent_session = students.filter(year=recent_year).order_by('session').first().session
            students = students.filter(year=recent_year, session=recent_session)
                
            students = students.order_by('roll_number')

            serializer = serializers.StudentSerializer(students, many=True)
            print

            for student_data in serializer.data:
                student_instance = models.Student.objects.get(primary_field=student_data['primary_field'])
                proctor_abbreviation = student_instance.proctor_abbreviation

                if proctor_abbreviation:
                    faculty_objects = models.Faculty.objects.filter(faculty_abbreviation=proctor_abbreviation)
                    if faculty_objects.exists():
                        proctor = faculty_objects.first()
                        proctor_data = {
                            'proctor_name': proctor.faculty_name,
                            'proctor_email': proctor.faculty_email,
                            'proctor_mobile_number': proctor.mobile_number,
                        }
                        student_data.update(proctor_data)
                    else:
                        student_data.update({
                            'proctor_name': None,
                            'proctor_email': None,
                            'proctor_mobile_number': None,
                        })
                else:
                    student_data.update({
                        'proctor_name': None,
                        'proctor_email': None,
                        'proctor_mobile_number': None,
                    })

            return Response(serializer.data)
        else:
            return Response([], status=status.HTTP_404_NOT_FOUND)

    def list(self, request, year=None, session=None, branch=None):
        students = models.Student.objects.all()
        current_year = request.query_params.get('current_year')
        print(current_year)

        if branch == 'undefined':
            branch = None

        if year:
            students = students.filter(year=year)
        if session:
            students = students.filter(session=session)
        if branch:
            students = students.filter(student_branch=branch)

        if current_year and current_year!='All':
            students = students.filter(current_year=current_year)
        students = students.order_by('roll_number')
        serializer = serializers.StudentSerializer(students, many=True)
        return Response(serializer.data)

    def recent(self, request, student_email=None):
        if student_email:
            student_instances = models.Student.objects.filter(email=student_email)

            if not student_instances.exists():
                return Response({"error": "No student found with this roll number"}, status=status.HTTP_404_NOT_FOUND)

            session_order = {'ODD': 0, 'EVEN': 1}
            sorted_students = sorted(student_instances, key=lambda student: (student.year, session_order[student.session]))
            most_recent_student = sorted_students[-1]
            serializer = serializers.StudentSerializer(most_recent_student)
            student_data = serializer.data.copy()

            try:
                proctor = models.Faculty.objects.get(faculty_abbreviation=most_recent_student.proctor_abbreviation)
                student_data['proctor_name'] = proctor.faculty_name
            except models.Faculty.DoesNotExist:
                student_data['proctor_name'] = None

            return Response(student_data)

        return Response({"error": "Roll number not provided"}, status=status.HTTP_400_BAD_REQUEST)
            
    def retrieve(self, request, student_email=None):
        try:
            student_instance = models.Student.objects.get(email=student_email)
            serializer = serializers.StudentSerializer(student_instance)
            return Response(serializer.data)
        except models.Student.DoesNotExist:
            return Response({"message": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        
        file = request.FILES.get('file')
        if not file:
            return Response({"message": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)
            
        csv_data = csv.reader(TextIOWrapper(file, encoding='utf-8'))
        next(csv_data, None)
        
        error_messages = set()
        validate = lambda x: x.strip().upper()

        for row in csv_data:
            if not any(cell.strip() for cell in row):
                continue
            
            for i, entry in enumerate(row):
                row[i] = validate(entry)
            
            year = validate(request.data.get("year"))
            session = validate(request.data.get("session"))
            
            student_branch = row[0]
            student_name = row[1]
            roll_number = row[2]
            email = row[3].lower()
            current_year = row[4]
            proctor_abbreviation = row[5]
            student_contact_no = row[6]
            parents_contact_no = row[7]
            parent_email_id = row[8].lower()
            division = row[9]
            ip_courses = [course for course in row[10:]]
            
            if not models.Branch.objects.filter(branch_abbreviation=student_branch).exists():
                error_messages.add(f"{student_branch} Branch Doesn't Exist in Database")
                continue
            
            if len(roll_number) != 11 or not roll_number.isdigit():
                error_messages.add(f"Invalid Roll Number format: {roll_number}")
                continue

            if not re.match(r'^[a-zA-Z0-9._%+-]+@somaiya.edu$', email):
                error_messages.add(f"{roll_number}'s email {email} is invalid")
                continue

            if not models.Faculty.objects.filter(faculty_abbreviation=proctor_abbreviation).exists():
                error_messages.add(f"{proctor_abbreviation} Faculty Doesn't Exist in Database")
                continue

            if len(student_contact_no)!=10 or not student_contact_no.isdigit():
                error_messages.add(f"Invalid Mobile Number format: {student_contact_no}")
                continue
            if len(parents_contact_no)!=10 or not parents_contact_no.isdigit():
                error_messages.add(f"Invalid Mobile Number format: {parents_contact_no}")
                continue
            
            if parent_email_id and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', parent_email_id):
                error_messages.add(f"{parent_email_id} is invalid")
                continue
            
            all_courses = models.Course.objects.filter(branch=student_branch)                    
            valid_courses = [course.course_code for course in all_courses]
            for course in ip_courses:
                if course and course not in valid_courses:
                    error_messages.add(f"{course} does not exist for {student_branch}") 
                    continue   
            
            
            primary_field = f"{year}|{session}|{roll_number}"
            try:
                student_instance = models.Student.objects.get(primary_field=primary_field)
            except models.Student.DoesNotExist:
                student_instance = None

            if student_instance:
                serializer = serializers.StudentPostSerializer(student_instance, data={
                    'student_branch' : student_branch,
                    'student_name' : student_name,
                    'email' : email,
                    'current_year': current_year,
                    'proctor_abbreviation' : proctor_abbreviation,
                    'student_contact_no' : student_contact_no,
                    'parents_contact_no' : parents_contact_no,
                    'parent_email_id' : parent_email_id,
                    'division' : division,
                    'course_1' : ip_courses[0],
                    'course_2' : ip_courses[1],
                    'course_3' : ip_courses[2],
                    'course_4' : ip_courses[3],
                    'course_5' : ip_courses[4],
                    'course_6' : ip_courses[5],
                    'course_7' : ip_courses[6],
                    'course_8' : ip_courses[7],
                    'course_9' : ip_courses[8],
                    'course_10' : ip_courses[9],
                    'course_11' : ip_courses[10],
                    'course_12' : ip_courses[11],
                    'course_13' : ip_courses[12],
                    'course_14' : ip_courses[13],
                    'course_15' : ip_courses[14],                          
                }, partial=True)
            else:     
                serializer = serializers.StudentPostSerializer(data={
                    'primary_field': primary_field, 
                    'student_branch' : student_branch,
                    'student_name' : student_name,
                    'roll_number' : roll_number,
                    'email' : email,
                    'current_year': current_year,
                    'proctor_abbreviation' : proctor_abbreviation,
                    'student_contact_no' : student_contact_no,
                    'parents_contact_no' : parents_contact_no,
                    'parent_email_id' : parent_email_id,
                    'year' : year,
                    'session' : session,
                    'division' : division,
                    'course_1' : ip_courses[0],
                    'course_2' : ip_courses[1],
                    'course_3' : ip_courses[2],
                    'course_4' : ip_courses[3],
                    'course_5' : ip_courses[4],
                    'course_6' : ip_courses[5],
                    'course_7' : ip_courses[6],
                    'course_8' : ip_courses[7],
                    'course_9' : ip_courses[8],
                    'course_10' : ip_courses[9],
                    'course_11' : ip_courses[10],
                    'course_12' : ip_courses[11],
                    'course_13' : ip_courses[12],
                    'course_14' : ip_courses[13],
                    'course_15' : ip_courses[14],  
                })

            if serializer.is_valid():  
                serializer.save()

                if not student_instance:
                    hashed_password = make_password(str(roll_number))
                    username = email.split('@')[0]
                    serializer3 = serializers.UserCredentialsSerializer(data={
                        'email' : email,
                        'password': hashed_password,
                        'role': "student", 
                        'username': username,
                    })

                    if serializer3.is_valid():
                        serializer3.save()

                for course in ip_courses:
                    if course:
                        try:
                            marks_instance = models.Marks.objects.get(course_code=course, roll_number=roll_number)
                        except models.Marks.DoesNotExist:
                            marks_instance = None

                        if not marks_instance:
                            models.Marks.objects.create(
                                year=year,
                                session=session,
                                branch=student_branch,
                                course_code=course,
                                division=division,
                                roll_number=roll_number,
                                student_name = student_name,
                            )
        if error_messages:
            return Response({
                "message": "Error adding CSV data.",
                "errors": error_messages
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "CSV data added to faculty models successfully."}, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        try:
            student_instance = models.Student.objects.get(pk=pk)
            email = serializers.StudentSerializer(student_instance).data.get('email')
            roll_number = serializers.StudentSerializer(student_instance).data.get('roll_number')
            marks_instances = models.Marks.objects.filter(roll_number=roll_number)
            user_instance = models.UserCredentials.objects.get(email=email)
            marks_instances.delete()
            user_instance.delete()
            student_instance.delete()
            return Response({"message": "Student deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except models.Student.DoesNotExist:
            return Response({"message": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

class StudentByProctorAbbreviation(generics.ListAPIView):
    def get_queryset(self):
        proctor_abbreviation = self.kwargs['abbreviation']
        return models.Student.objects.filter(proctor_abbreviation__faculty_abbreviation=proctor_abbreviation)

class CourseViewSet(viewsets.ViewSet):
    def edit(self, request):
        course_code = request.data.get('course_code')
        try:
            course_instance = models.Course.objects.get(course_code=course_code)
            course_instance.course_name = request.data.get('course_name', course_instance.course_name)
            course_instance.course_abbreviation = request.data.get('course_abbreviation', course_instance.course_abbreviation)
            course_instance.sem = request.data.get('sem', course_instance.sem)
            course_instance.scheme_name = request.data.get('scheme_name', course_instance.scheme_name)
            course_instance.hours = request.data.get('hours', course_instance.hours)
            course_instance.credit = request.data.get('credit', course_instance.credit)
            
            course_instance.save()
            
            serializer = serializers.CourseSerializer(course_instance)
            return Response(serializer.data)
        except models.Course.DoesNotExist:
            return Response({"error": "Course not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def list(self, request, branch=None):
        if branch:
            courses = models.Course.objects.filter(branch=branch).order_by('course_name')
        else:
            courses = models.Course.objects.all().order_by('course_name')

        serializer = serializers.CourseSerializer(courses, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            course_instance = models.Course.objects.get(pk=pk)
            serializer = serializers.CourseSerializer(course_instance)
            return Response(serializer.data)
        except models.Course.DoesNotExist:
            return Response({"message": "Course not found."}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"message": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)
        
        csv_data = csv.reader(TextIOWrapper(file, encoding='utf-8'))
        next(csv_data, None)
        
        error_messages = set()
        validate = lambda x: x.strip().upper()

        for row in csv_data:
            for i, entry in enumerate(row):
                row[i] = validate(entry)

            branch = row[0]
            course_code = row[1]
            course_abbreviation = row[2]
            course_name = row[3]
            sem = row[4]
            scheme_name = row[5]
            credit = row[6]
            hours = row[7]
            tutorial = row[8]
            
            if not models.Branch.objects.filter(branch_abbreviation=branch).exists():
                error_messages.add(f"{branch} Doesn't Exist in Database")
                continue
            if len(course_code) != 10:
                error_messages.add(f"{row[1]} is an invalid Course Code.")
                continue
            if not sem.isdigit() and len(sem) != 1:
                error_messages.add(f"Invalid Semester Field: {sem}")
                continue
            if not credit.isdigit() and credit:
                error_messages.add(f"Invalid Credit Field a: {credit}")
                continue
            if not hours.isdigit() and hours:
                error_messages.add(f"Invalid Hours Field: {hours}")
                continue
            
            sem = int(sem)
            if credit:
                credit = int(credit)
            if hours:
                hours = int(hours)
            
            try:
                course_instance = models.Course.objects.get(course_code=course_code)
            except models.Course.DoesNotExist:
                course_instance = None

            if course_instance:
                serializer = serializers.CourseSerializer(course_instance, data={
                    'branch' : branch,
                    'course_abbreviation': course_abbreviation,
                    'course_name' : course_name,
                    'sem' : sem,
                    'scheme_name' : scheme_name,
                    'credit' : credit,
                    'hours' : hours,
                    'tutorial' : tutorial,
                }, partial=True)
            else:
                serializer = serializers.CourseSerializer(data={
                    
                    'branch' : branch,
                    'course_code' : course_code,
                    'course_abbreviation': course_abbreviation,
                    'course_name' : course_name,
                    'sem' : sem,
                    'scheme_name' : scheme_name,
                    'credit' : credit,
                    'hours' : hours,
                    'tutorial' : tutorial,
                })

            if serializer.is_valid():
                serializer.save()

        if error_messages:
            return Response({
                "message": "Error adding CSV data.",
                "errors": error_messages
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "CSV data added to faculty models successfully."}, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        try:
            course_instance = models.Course.objects.get(pk=pk)
            course_instance.delete()
            return Response({"message": "Course deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except models.Course.DoesNotExist:
            return Response({"message": "Course not found."}, status=status.HTTP_404_NOT_FOUND)
    
    def get_course_details(request, course_code):
        try:
            course = models.Course.objects.get(course_code=course_code)
            tutorial = course.tutorial
            return Response({'tutorial': tutorial})
        except models.Course.DoesNotExist:
            return Response({'error': 'Course not found'}, status=404)

class CourseAllotmentViewSet(viewsets.ViewSet):
    def list(self, request, year=None, session=None, branch=None):
        courses_allotments = models.CourseAllotment.objects.all()

        if year:
            #! TEMP FIX
            year = year.replace("_", "-")
            courses_allotments = courses_allotments.filter(year=year)
        if session:
            courses_allotments = courses_allotments.filter(session=session)
        if branch:
            # Extract course codes from the filtered CourseAllotment objects
            course_codes = courses_allotments.values_list('course_code', flat=True)
            
            # Fetch the courses based on the course codes
            courses = models.Course.objects.filter(course_code__in=course_codes)
            
            # Filter courses again based on the branch
            courses = courses.filter(branch=branch)

            # Get the course codes from the filtered courses
            filtered_course_codes = courses.values_list('course_code', flat=True)
            
            # Filter the CourseAllotment objects again based on the filtered course codes
            courses_allotments = courses_allotments.filter(course_code__in=filtered_course_codes)

        serializer = serializers.CourseAllotmentSerializer(courses_allotments, many=True)
        return Response(serializer.data)



        serializer = serializers.CourseAllotmentSerializer(courses_allotments, many=True)
        return Response(serializer.data)
    
    def list2(self, request, abbreviation=None, year=None, session=None):
        courses_allotments = models.CourseAllotment.objects.all()

        if abbreviation:
            courses_allotments = courses_allotments.filter(faculty_abbreviation=abbreviation, year=year, session=session)

            if not courses_allotments.exists():
                courses_allotments = models.CourseAllotment.objects.all()
                courses_allotments = courses_allotments.filter(staff_abbreviation=abbreviation, year=year, session=session)
        

        serializer = serializers.CourseAllotmentSerializer(courses_allotments, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            course_allotment_instance = models.CourseAllotment.objects.get(pk=pk)
            serializer = serializers.CourseAllotmentSerializer(course_allotment_instance)
            return Response([serializer.data])
        except models.CourseAllotment.DoesNotExist:
            return Response({"message": "Course Allotment not found."}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"message": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)
        
        csv_data = csv.reader(TextIOWrapper(file, encoding='utf-8'))
        next(csv_data, None)
        
        error_messages = set()
        validate = lambda x: x.strip().upper()

        for row in csv_data:
            if not any(cell.strip() for cell in row):
                continue
            
            for i, entry in enumerate(row):
                row[i] = validate(entry)

            course = models.Course.objects.filter(course_code=row[0]).first()

            year = validate(request.data.get("year"))
            session = validate(request.data.get("session"))
            course_code = row[0]
            course_abbreviation = row[1]
            faculty_abbreviation = row[2]
            staff_abbreviation = row[3]

            if course:
                course_name = course.course_name
            else:
                error_messages.add(f"{course_code} is Invalid or Doesn't Exist")
                continue
            if not models.Course.objects.filter(course_code=course_code, course_abbreviation=course_abbreviation).exists():
                error_messages.add(f"{course_code}-{course_abbreviation} are not related")
                continue
            if not models.Faculty.objects.filter(faculty_abbreviation=faculty_abbreviation).exists():
                error_messages.add(f"{faculty_abbreviation} Doesn't exist in database")
                continue
            if not models.Staff.objects.filter(staff_abbreviation=staff_abbreviation).exists():
                error_messages.add(f"{staff_abbreviation} Doesn't exist in database")
                continue
            
            try:
                course_allotment_instance = models.CourseAllotment.objects.get(
                    year=year, session=session, course_code=course_code
                )
            except models.CourseAllotment.DoesNotExist:
                course_allotment_instance = None

            if course_allotment_instance:
                serializer = serializers.CourseAllotmentSerializer(course_allotment_instance, data={
                    'course_name': course_name,
                    'course_abbreviation': course_abbreviation,
                    'faculty_abbreviation': faculty_abbreviation,
                    'staff_abbreviation': staff_abbreviation,
                }, partial=True)
            else:
                serializer = serializers.CourseAllotmentSerializer(data={
                    'course_code': course_code,
                    'course_name': course_name,
                    'year': year,
                    'session': session,
                    'faculty_abbreviation': faculty_abbreviation,
                    'course_abbreviation': course_abbreviation,
                    'staff_abbreviation': staff_abbreviation,
                })

            if serializer.is_valid():
                serializer.save()
            else:
                error_messages.add(f"Error with row {row[0].upper()}: {serializer.errors}")

        if error_messages:
            return Response({
                "message": "Error adding CSV data.",
                "errors": error_messages
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "CSV data added to faculty models successfully."}, status=status.HTTP_201_CREATED)

    def destroy(self, request, faculty_abbreviation=None,course_code=None):
        try:
            course_allotment_instance = models.CourseAllotment.objects.get(faculty_abbreviation=faculty_abbreviation,course_code=course_code)
            course_allotment_instance.delete()
            return Response({"message": "Course  Allotment deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except models.CourseAllotment.DoesNotExist:
            return Response({"message": "Course Allotment not found."}, status=status.HTTP_404_NOT_FOUND)

class MarksViewSet(viewsets.ViewSet):
    def list(self, request, year=None, session=None, course_code=None, roll_number=None):
        # Fetch all marks with the given filters
        marks = models.Marks.objects.all()
        if roll_number:
            marks = marks.filter(roll_number=roll_number)
        if course_code:
            marks = marks.filter(course_code=course_code)
        if year:
            marks = marks.filter(year=year)
        if session:
            marks = marks.filter(session=session)

        # Serialize the marks
        serializer = serializers.MarksSerializer(marks, many=True)

        # Collect all course codes from the serialized data
        course_codes = set(item['course_code'] for item in serializer.data)
        
        # Fetch all courses with the collected course codes
        courses = models.Course.objects.filter(course_code__in=course_codes).values('course_code', 'course_name')
        course_dict = {course['course_code']: course['course_name'] for course in courses}

        # Add course names to each mark item
        for item in serializer.data:
            course_code = item['course_code']
            item['course_name'] = course_dict.get(course_code, 'Unknown Course')

        return Response(serializer.data)

    def list2(self, request, roll_number=None):
        marks = models.Marks.objects.all()
        if roll_number:
            marks = marks.filter(roll_number=roll_number)
        serializer = serializers.MarksSerializer(marks, many=True)
        
        unique_year_sessions = {(item['year'], item['session']) for item in serializer.data}  
        unique_year_sessions_list = [{'year': year, 'session': session} for year, session in unique_year_sessions]
        return Response(unique_year_sessions_list)

    def retrieve(self, request, course_code=None, roll_number=None):
        try:
            mark_instance = models.Marks.objects.get(course_code=course_code, roll_number=roll_number)
            serializer = serializers.MarksSerializer(mark_instance)
            return Response(serializer.data)
        except models.Marks.DoesNotExist:
            return Response({"message": "Marks record not found."}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        exam = request.data.get('exam') 

        if not exam:
            return Response({'error': 'Exam information is required.'}, status=status.HTTP_400_BAD_REQUEST)


        file = request.FILES.get('file')
        if file:
            
            csv_data = csv.reader(TextIOWrapper(file, encoding='utf-8'))
            
            next(csv_data, None)

            for row in csv_data:

                year = row[0]
                session = row[1]
                branch = row[2]
                course_code = row[3]
                division = row[4]
                student_name =row[5]
                roll_number = row[6]
                marks_value = row[7]

                try:
                    mark_instance = models.Marks.objects.get(course_code=course_code,roll_number=roll_number)
                except models.Marks.DoesNotExist:
                    mark_instance = None


                if mark_instance:
                    
                    serializer = serializers.MarksSerializer(mark_instance, data={
                        
                        'year': year,
                        'session': session,
                        'branch': branch, 
                        'division': division,
                        'student_name': student_name,
                        exam: marks_value,
                        

                    
                    }, partial=True)
                else:
                    
                    serializer = serializers.MarksSerializer(data={

                        'year': year,
                        'session': session,
                        'branch': branch, 
                        'course_code': course_code,
                        'division': division,
                        'student_name': student_name,
                        'roll_number': roll_number,
                        exam: marks_value,
                        
                        
                    })

                if serializer.is_valid():
                    serializer.save()


            return Response({"message": "CSV data added to Marks models successfully."}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, course_code=None, roll_number=None):
        try:
            mark_instance = models.Marks.objects.get(course_code=course_code, roll_number=roll_number)
            mark_instance.delete()
            return Response({"message": "Marks data deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except models.Marks.DoesNotExist:
            return Response({"message": "Marks data not found."}, status=status.HTTP_404_NOT_FOUND)

    def delete_exam_marks(self, request, exam, course_code=None, roll_number=None):
        try:
            mark_instance = models.Marks.objects.get(course_code=course_code, roll_number=roll_number)
            
            setattr(mark_instance, exam, None)
            mark_instance.save()
            return Response({"message": f"{exam} marks deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except models.Marks.DoesNotExist:
            return Response({"message": "Marks data not found."}, status=status.HTTP_404_NOT_FOUND)

class DownloadExamCSV(APIView):
    def get(self, request, exam, course_code):
        
        marks = models.Marks.objects.filter(course_code=course_code)

        headers = ['year', 'session', 'branch', 'course_code', 'division', 'student_name', 'roll_number', 'marks']

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{exam}_marks_{course_code}_{timezone.now().strftime("%Y%m%d%H%M%S")}.csv"'

        writer = csv.writer(response)
        writer.writerow(headers)
        for mark in marks:
            writer.writerow([
                mark.year,
                mark.session,
                mark.branch,
                mark.course_code,
                mark.division,
                mark.student_name,
                mark.roll_number,
                getattr(mark, exam)
            ])

        return response

class AcademicYearViewSet(viewsets.ViewSet):
    def list(self,request):
        years=models.AcademicYear.objects.all().order_by('-year')
        print(years)
        
        serializer = serializers.AcademicYearSerializer(years, many=True)
        return Response(serializer.data)

    def create(self,request):
        year = request.data.get('year')
        session = request.data.get('session')

        if not year:
            return Response({'error': 'Year information is required.'}, status=status.HTTP_400_BAD_REQUEST)
        elif not session:
            return Response({'error': 'Session information is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if models.AcademicYear.objects.filter(year=year, session=session).exists():
            return Response({'error': 'This Year Session already exists'}, status=status.HTTP_400_BAD_REQUEST)

        
        if year and session:
            serializer = serializers.AcademicYearSerializer(data={
                'year':year,
                'session':session,
            })

            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Academic year added to Marks models successfully."}, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, year=None, session=None):
        try:
            academicyear_instance = models.AcademicYear.objects.get(year=year, session=session)
            academicyear_instance.delete()
            return Response({"message": "Attendance data deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except models.AcademicYear.DoesNotExist:
            return Response({"message": "Attendance data not found."}, status=status.HTTP_404_NOT_FOUND)

class DownloadAllExamCSV(APIView):
    def get(self, request, course_code, year, session):
        
        marks = models.Marks.objects.filter(course_code=course_code, year=year, session=session)

        headers = ['year', 'session', 'branch', 'course_code', 'division', 'student_name', 'roll_number','marks']

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="marks_{course_code}_{timezone.now().strftime("%Y%m%d%H%M%S")}.csv"'

        writer = csv.writer(response)
        writer.writerow(headers)
        for mark in marks:
            writer.writerow([
                mark.year,
                mark.session,
                mark.branch,
                mark.course_code,
                mark.division,
                mark.student_name,
                mark.roll_number,
            ])

        return response

class AttendanceViewSet(viewsets.ViewSet):
    def retrieve(self, request, course_code=None, roll_number=None):
        try:
            attendance_instance = models.Attendance.objects.get(course_code=course_code, roll_number=roll_number)
            serializer = serializers.AttendanceSerializer(attendance_instance)
            return Response(serializer.data)
        except models.Attendance.DoesNotExist:
            return Response({"message": "Attendance record not found."}, status=status.HTTP_404_NOT_FOUND)

    def list(self, request, course_code, year, session):
        attendance = models.Attendance.objects.filter(course_code=course_code, year=year, session=session)
        response_data = []

        for record in attendance:
            student_data = {
            "student_name": record.student_name,
            "roll_number": record.roll_number,
            "attendance": {},
            }

            for month in ["january", "february", "march","april","may","june","july","august","september","october","november", "december"]:  # Iterate through all months
                attendance_value = getattr(record, month, None)  
                if attendance_value is not None:
                    if record.class_type == "TH/PR":
                        student_data["attendance"][month] = attendance_value
                    elif record.class_type == "TUT":
                        student_data["attendance"][month + "_TUT"] = attendance_value 

            response_data.append(student_data)

        return Response(response_data)

    def create(self, request):
        month = request.data.get('month')
        class_type = request.data.get('class')
        if not month:
            return Response({'error': 'Month information is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES.get('file')
        if file:
            csv_data = csv.reader(TextIOWrapper(file, encoding='utf-8'))
            next(csv_data, None)

            for row in csv_data:
                year = row[0]
                session = row[1]
                branch = row[2]
                course_code = row[3]
                student_name = row[4]
                roll_number = row[5]
                month_attendance_value = row[6]

                try:
                    attendance_instance = models.Attendance.objects.get(course_code=course_code, roll_number=roll_number, class_type=class_type)
                    setattr(attendance_instance, month, month_attendance_value)
                except models.Attendance.DoesNotExist:
                    attendance_instance = models.Attendance(
                        year=year,
                        session=session,
                        branch=branch,
                        course_code=course_code,
                        student_name=student_name,
                        roll_number=roll_number,
                        class_type=class_type,
                        **{month: month_attendance_value}
                    )

                attendance_instance.save()

            return Response({"message": "CSV data added to Attendance models successfully."}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, course_code=None, roll_number=None):
        try:
            attendance_instance = models.Attendance.objects.get(course_code=course_code, roll_number=roll_number)
            attendance_instance.delete()
            return Response({"message": "Attendance data deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except models.Attendance.DoesNotExist:
            return Response({"message": "Attendance data not found."}, status=status.HTTP_404_NOT_FOUND)

    def delete_month_attendance(self, request, month, course_code=None, roll_number=None):
        try:
            attendance_instance = models.Attendance.objects.get(course_code=course_code, roll_number=roll_number)
            setattr(attendance_instance, month, None)
            attendance_instance.save()
            return Response({"message": f"{month} attendance deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except models.Marks.DoesNotExist:
            return Response({"message": "Attendance data not found."}, status=status.HTTP_404_NOT_FOUND)
    
    def get_student_attendance(self, request, course_code=None, roll_number=None):
        try:
            attendance_records = models.Attendance.objects.filter(course_code=course_code, roll_number=roll_number)
            if not attendance_records.exists():
                return Response({"th_pr": "-", "tut": "-"})

            total_th_pr = 0
            total_tut = 0
            count_th_pr = 0
            count_tut = 0

            for record in attendance_records:
                monthly_values = [
                    record.january, record.february, record.march, record.april,
                    record.may, record.june, record.july, record.august,
                    record.september, record.october, record.november, record.december
                ]
                valid_values = [value for value in monthly_values if value is not None]

                if record.class_type == 'TH/PR':
                    total_th_pr += sum(valid_values)
                    count_th_pr += len(valid_values)
                elif record.class_type == 'TUT':
                    total_tut += sum(valid_values)
                    count_tut += len(valid_values)

            average_th_pr = total_th_pr / count_th_pr if count_th_pr else "-"
            average_tut = total_tut / count_tut if count_tut else "-"

            return Response({"th_pr": average_th_pr, "tut": average_tut})
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class DownloadMonthAttendanceCSV(APIView):
    def get(self, request, month, course_code):
        
        attendance_instance = models.Attendance.objects.filter(course_code=course_code)

        headers = ['year', 'session', 'branch', 'course_code', 'course_name', 'student_name', 'roll_number', 'month']

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{month}_attendance_{course_code}_{timezone.now().strftime("%Y%m%d%H%M%S")}.csv"'

        writer = csv.writer(response)
        writer.writerow(headers)
        for attendance in attendance_instance:
            writer.writerow([
                attendance.year,
                attendance.session,
                attendance.branch,
                attendance.course_code,
                attendance.course_name,
                attendance.student_name,
                attendance.roll_number,
                getattr(attendance, month)
                
            ])

        return response

class DownloadAllMonthAttendanceCSV(APIView):
    def get(self, request, course_code,year,session):
        
        attendance_instance = models.Attendance.objects.filter(course_code=course_code,year=year,session=session)

        headers = ['Year', 'Session', 'Branch', 'Course Code', 'Student Name', 'Roll Number', 'Class', 'Attendance']

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="attendance_{course_code}_{timezone.now().strftime("%Y%m%d%H%M%S")}.csv"'

        writer = csv.writer(response)
        writer.writerow(headers)
        for attendance in attendance_instance:
            writer.writerow([
                attendance.year,
                attendance.session,
                attendance.branch,
                attendance.course_code,
                attendance.student_name,
                attendance.roll_number,
                attendance.class_type,
            ])

        return response

class StudentByProctorAbbreviation(generics.ListAPIView):
    serializer_class = serializers.StudentSerializer

    def get_queryset(self):
        proctor_abbreviation = self.kwargs['abbreviation']
        return models.Student.objects.filter(proctor_abbreviation__faculty_abbreviation=proctor_abbreviation)

class DownloadCSV(APIView):
    allowed_methods = ['GET', 'POST']

    def get(self, request, model):
        if model == 'Faculty':
            queryset = models.Faculty.objects.none()  
            serializer_class = serializers.FacultySerializer
        elif model == 'Staff':
            queryset = models.Staff.objects.none()  
            serializer_class = serializers.StaffSerializer
        elif model == 'Student':
            queryset = models.Student.objects.none()  
            serializer_class = serializers.StudentSerializer
        elif model == 'Course':
            queryset = models.Course.objects.none()  
            serializer_class = serializers.CourseSerializer
        elif model == 'CourseAllotment':
            queryset = models.CourseAllotment.objects.none()
            serializer_class = serializers.CourseAllotmentSerializer
        elif model == 'Marks':
            queryset = models.Marks.objects.none()
            serializer_class = serializers.MarksSerializer
        elif model == 'Attendance':
            queryset = models.Attendance.objects.none()
            serializer_class = serializers.AttendanceSerializer
        else:
            return Response({'message': 'Invalid model name.'}, status=400)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(model)


        serializer = serializer_class(queryset, many=True)

        field_names = ['DEPARTMENT', 'EMPLOYEE CODE', 'FACULTY ABBREVIATION', 'FACULTY NAME',
               'FACULTY EMAIL', 'EXPERIENCE', 'POST', 'MOBILE NUMBER'] if model == 'Faculty' else \
              ['DEPARTMENT', 'EMPLOYEE CODE', 'STAFF ABBREVIATION', 'STAFF NAME',
               'STAFF EMAIL', 'EXPERIENCE', 'POST', 'MOBILE NUMBER'] if model == 'Staff' else \
              ['BRANCH', 'NAME', 'ROLL NUMBER', 'EMAIL', ' CURRENT YEAR', 'PROCTOR ABBREVIATION',
               'STUDENT CONTACT NO', 'PARENT CONTACT NO', 'PARENT EMAIL ID', 'DIVISION', 'COURSE 1', 'COURSE 2', 'COURSE 3', 'COURSE 4', 'COURSE 5', 'COURSE 6', 
               'COURSE 7', 'COURSE 8', 'COURSE 9', 'COURSE 10', 'COURSE 11', 'COURSE 12', 
               'COURSE 13', 'COURSE 14', 'COURSE 15'] if model == 'Student' else \
              ['BRANCH', 'COURSE CODE', 'COURSE ABBREVIATION', 'COURSE NAME', 'SEM',
               'SCHEME NAME', 'CREDIT', 'HOURS', 'TUTORIAL'] if model == 'Course' else \
              ['COURSE CODE', 'COURSE ABBREVIATION', 
               'FACULTY ABBREVIATION', 'STAFF ABBREVIATION'] if model == 'CourseAllotment' else \
              ['YEAR', 'SESSION', 'BRANCH', 'COURSE CODE', 'DIVISION', 'STUDENT NAME', 
               'ROLL NUMBER', 'MARKS'] if model == 'Marks' else \
              ['YEAR', 'SESSION', 'BRANCH', 'COURSE CODE', 'COURSE NAME', 'STUDENT NAME', 
               'ROLL NUMBER', 'MONTH'] if model == 'Attendance' else []


        writer = csv.DictWriter(response, fieldnames=field_names)
        writer.writeheader()

        return response

class StudentAchievementViewSet(viewsets.ViewSet):

    def list(self, request, roll_number=None):
        if roll_number is not None:
            achievements = models.StudentAchievement.objects.filter(roll_number=roll_number, approved='1')
            student = models.Student.objects.filter(roll_number=roll_number).first()
            student_serializer = serializers.StudentSerializer(student)

            if achievements.exists():
                serializer = serializers.StudentAchievementSerializer(achievements, many=True)
                student_name = student_serializer.data.get('student_name', '')
                response_data = {
                    'achievements': serializer.data,
                    'student_name': student_name,
                }

                return Response(response_data)
            else:
                return Response({"message": "Student Achievement data not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"message": "Roll number is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    def unapproved(self, request, proctor=None):
        if proctor:
            unapproved = models.StudentAchievement.objects.filter(approved='0', proctor=proctor)
        
        serializer = serializers.StudentAchievementSerializer(unapproved, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            achievement_instance = models.StudentAchievement.objects.get(pk=pk)
            serializer = serializers.StudentAchievementSerializer(achievement_instance)
            return Response(serializer.data)
        except models.StudentAchievement.DoesNotExist:
            return Response({"message": "Student Achievement data not found."}, status=status.HTTP_404_NOT_FOUND)
    
    def create(self, request):
        serializer = serializers.StudentAchievementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        try:
            achievement_instance = models.StudentAchievement.objects.get(pk=pk)
            achievement_instance.delete()
            return Response({"message": "Student Achievement data deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except models.StudentAchievement.DoesNotExist:
            return Response({"message": "Student Achievement data not found."}, status=status.HTTP_404_NOT_FOUND)
    
    def approve(self, request, achievement_id):
        try:
            achievement_instance = models.StudentAchievement.objects.get(id=achievement_id)
            achievement_instance.approved = "1"
            achievement_instance.save()
        except models.StudentAchievement.DoesNotExist:
            return Response({"message": "Student Achievement not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"message": "Student Achievement updated."}, status=status.HTTP_200_OK)

    def reject(self, request, achievement_id):
        try:
            achievement_instance = models.StudentAchievement.objects.get(id=achievement_id)
        except models.StudentAchievement.DoesNotExist:
            return Response({"message": "Student Achievement not found."}, status=status.HTTP_404_NOT_FOUND)

        reason = request.data.get('reason', '')
        sender_email = request.data.get('sender')
        roll_number = achievement_instance.roll_number
        students = models.Student.objects.filter(roll_number=roll_number)
        unique_emails = set(student.email for student in students)

        achievement_instance.delete()
        for email in unique_emails:
            subject = 'Student Achievement Rejection'
            message = f'Dear Student,\n\nYour achievement has been rejected for the following reason:\n\n{reason}\n\nRegards,\nAdmin'
            send_mail(subject, message, settings.EMAIL_HOST_USER, [email])

        return Response({"message": "Student Achievement with roll number {} rejected with reason: {}".format(roll_number, reason)}, status=status.HTTP_200_OK)

class StudentInternshipViewSet(viewsets.ViewSet):
    def list(self, request, roll_number=None):
        if roll_number is not None:
            internships = models.StudentInternship.objects.filter(roll_number=roll_number)
            student = models.Student.objects.filter(roll_number=roll_number).first()
            student_serializer = serializers.StudentSerializer(student)
            if internships.exists():
                serializer = serializers.StudentInternshipSerializer(internships, many=True)
                student_name = student_serializer.data.get('student_name', '')
                response_data = {
                    'internship': serializer.data,
                    'student_name': student_name,
                }
                return Response(response_data)
            else:
                return Response({"message": "Student Internship data not found inside list."}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"message": "Roll number is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    def unapproved(self, request, proctor=None):
        if proctor:
            unapproved = models.StudentInternship.objects.filter(approved='0', proctor=proctor)
        
        serializer = serializers.StudentInternshipSerializer(unapproved, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            internship_instance = models.StudentInternship.objects.get(pk=pk)
            serializer = serializers.StudentInternshipSerializer(internship_instance)
            return Response(serializer.data)
        except models.StudentInternship.DoesNotExist:
            return Response({"message": "Student Internship data not found."}, status=status.HTTP_404_NOT_FOUND)
    
    def create(self, request):
        serializer = serializers.StudentInternshipSerializer(data=request.data)
        print('here')
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        try:
            internship_instance = models.StudentInternship.objects.get(pk=pk)
            internship_instance.delete()
            return Response({"message": "Student Internship data deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except models.StudentInternship.DoesNotExist:
            return Response({"message": "Student Internship data not found."}, status=status.HTTP_404_NOT_FOUND)
    
    def approve(self, request, internship_id):
        try:
            internship_instance = models.StudentInternship.objects.get(id=internship_id)
            internship_instance.approved = "1"
            internship_instance.save()
        except models.StudentInternship.DoesNotExist:
            return Response({"message": "Student Internship not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"message": "Student Internship updated."}, status=status.HTTP_200_OK)
    
    def reject(self, request, internship_id):
        try:
            achievement_instance = models.StudentInternship.objects.get(id=internship_id)
        except models.StudentAchievement.DoesNotExist:
            return Response({"message": "Student Achievement not found."}, status=status.HTTP_404_NOT_FOUND)

        reason = request.data.get('reason', '')
        sender_email = request.data.get('sender')
        roll_number = achievement_instance.roll_number
        students = models.Student.objects.filter(roll_number=roll_number)
        unique_emails = set(student.email for student in students)

        achievement_instance.delete()
        for email in unique_emails:
            subject = 'Student Achievement Rejection'
            message = f'Dear Student,\n\nYour achievement has been rejected for the following reason:\n\n{reason}\n\nRegards,\nAdmin'
            send_mail(subject, message, settings.EMAIL_HOST_USER, [email])


        return Response({"message": "Student Achievement with roll number {} rejected with reason: {}".format(roll_number, reason)}, status=status.HTTP_200_OK)

class UserLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = models.UserCredentials.objects.get(username=username)
            print(user)

            if check_password(password, user.password):
                tokens = user.get_tokens()
                return Response({
                    'role': user.role,
                    'email': user.email,
                    'username': user.username,
                    'access': tokens['access'],
                    'refresh': tokens['refresh'],
                })
            else:
                return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)
        except models.UserCredentials.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class UserLogout(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return Response({'error': 'Refresh token is required'}, status=400)

            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=205)
        except Exception as e:
            print(f"Error blacklisting token: {e}")
            return Response({'error': 'Error logging out'}, status=400)

class ChangePassword(viewsets.ViewSet):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email not provided'}, status=status.HTTP_400_BAD_REQUEST)

        user = models.UserCredentials.objects.filter(email=email).first()
        if not user:
            return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)

        otp = random.randint(100000, 999999)
        cache.set(email, otp, timeout=300)

        # Send OTP via email
        subject = 'Your Password Reset OTP'
        message = f'Your OTP for resetting the password is {otp}. It is valid for 5 minutes.'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]

        try:
            send_mail(subject, message, from_email, recipient_list)
        except Exception as e:
            return Response({'error': f'Failed to send email: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': 'OTP sent to email'}, status=status.HTTP_200_OK)

    def verify_otp(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email or not otp:
            return Response({'error': 'Email and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)

        cached_otp = cache.get(email)

        if cached_otp is None:
            return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)

        if str(cached_otp) != str(otp):
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'OTP verified'}, status=status.HTTP_200_OK)
    
    def reset_password(self, request):
        email = request.data.get('email')
        new_password = request.data.get('newPassword')

        try:
            user = models.UserCredentials.objects.get(email=email)
        except models.UserCredentials.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        hashed_password = make_password(new_password)
        user.password = hashed_password
        user.save()
        cache.delete(email)

        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)

class UserDetailView(APIView):
  permission_classes = [IsAuthenticated]

  def get(self, request):
    user = request.user
    return Response({
      'email': user.email,
      'first_name': user.first_name,
      'last_name': user.last_name,
      'role': user.role,  # Assuming you have a role field
    })