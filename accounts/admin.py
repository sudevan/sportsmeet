from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User, Department, UserRole
from accounts.models import Student


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User

    list_display = ("email", "role", "department", "is_active")
    list_filter = ("role", "department", "is_active")
    search_fields = ("email",)
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("full_name", "department", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "password1", "password2", "role"),
        }),
    )

    filter_horizontal = ()


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "register_number", "department", "semester", "gender")
    list_filter = ("department", "semester", "gender")
    search_fields = ("full_name", "register_number")
