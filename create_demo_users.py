import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User, UserRole, Department, Gender

def create_demo_data():
    # Create Departments
    cs_dept, _ = Department.objects.get_or_create(name="Computer Science")
    me_dept, _ = Department.objects.get_or_create(name="Mechanical Engineering")
    ec_dept, _ = Department.objects.get_or_create(name="Electronics and Communication")

    password = "password123"

    users_data = [
        {
            "email": "faculty_coord@example.com",
            "full_name": "Dr. Alice Smith",
            "role": UserRole.FACULTY_COORDINATOR,
            "department": cs_dept,
            "gender": Gender.FEMALE,
        },
        {
            "email": "student_coord@example.com",
            "full_name": "Bob Johnson",
            "role": UserRole.STUDENT_COORDINATOR,
            "department": cs_dept,
            "gender": Gender.MALE,
            "register_number": "CS001",
        },
        {
            "email": "faculty@example.com",
            "full_name": "Prof. Charlie Brown",
            "role": UserRole.FACULTY,
            "department": me_dept,
            "gender": Gender.MALE,
        },
        {
            "email": "student@example.com",
            "full_name": "Diana Ross",
            "role": UserRole.STUDENT,
            "department": me_dept,
            "gender": Gender.FEMALE,
            "register_number": "ME001",
        }
    ]

    for data in users_data:
        email = data.pop("email")
        user, created = User.objects.get_or_create(email=email, defaults=data)
        if created:
            user.set_password(password)
            user.save()
            print(f"Created {user.role}: {email}")
        else:
            print(f"User {email} already exists")

    # Update Department coordinators
    cs_dept.faculty_coordinator = User.objects.get(email="faculty_coord@example.com")
    cs_dept.student_coordinator = User.objects.get(email="student_coord@example.com")
    cs_dept.save()

if __name__ == "__main__":
    create_demo_data()
