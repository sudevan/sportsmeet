from django import forms 
from .models import Student, User, UserRole, Department

class StudentBulkUploadForm(forms.Form):
    csv_file = forms.FileField()
    
    
class ManualStudentAddForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "full_name",
            "register_number",
            "gender",
            "department",
            "semester",
        ]

        
        
class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)