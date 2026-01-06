from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin


class UserRole(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    FACULTY_COORDINATOR = "FACULTY_COORDINATOR", "Faculty Coordinator"
    STUDENT_COORDINATOR = "STUDENT_COORDINATOR", "Student Coordinator"
    FACULTY = "FACULTY", "Faculty"


class Gender(models.TextChoices):
    MALE = "MALE", "Male"
    FEMALE = "FEMALE", "Female"



class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name



# -------------------------
# STAFF USER (LOGIN USERS)
# -------------------------
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("role", UserRole.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=32, choices=UserRole.choices)
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = "email"

    def __str__(self):
        return self.email


# -------------------------
# STUDENT (NO LOGIN)
# -------------------------
class Student(models.Model):
    full_name = models.CharField(max_length=255)
    register_number = models.CharField(max_length=50, unique=True)
    gender = models.CharField(max_length=10, choices=Gender.choices)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    semester = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.full_name} ({self.register_number})"
