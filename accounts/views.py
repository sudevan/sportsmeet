import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.http import HttpResponseForbidden
from django.db.models import Q

from .models import User, Department, UserRole
from .forms import StudentBulkUploadForm, ManualStudentAddForm, LoginForm
from meet.models import Event, EventStatus, Meet, MeetEvent, MeetStatus, Registration




@login_required
def home(request):
    return render(request, "accounts/home.html")




def is_admin_or_coordinator(user):
    return user.role in [
        UserRole.ADMIN,
        UserRole.FACULTY_COORDINATOR,
        UserRole.STUDENT_COORDINATOR,
    ]


def get_user_department(user):
    if user.role in (
        UserRole.FACULTY_COORDINATOR,
        UserRole.STUDENT_COORDINATOR,
    ):
        return user.department
    return None


@login_required
def student_bulk_upload(request):
    if not is_admin_or_coordinator(request.user):
        return HttpResponseForbidden("Not allowed")

    redirect_role = None  # track highest role uploaded

    if request.method == "POST":
        form = StudentBulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES["csv_file"]
            decoded = csv_file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded)

            for row in reader:
                department, _ = Department.objects.get_or_create(
                    name=row["department"]
                )

                # Gender
                gender = row.get("gender", "").strip().upper()
                if gender not in ("MALE", "FEMALE"):
                    gender = None

                # Role (default STUDENT)
                role = row.get("role", "STUDENT").strip().upper()
                if role not in (
                    UserRole.STUDENT,
                    UserRole.STUDENT_COORDINATOR,
                    UserRole.FACULTY_COORDINATOR,
                ):
                    role = UserRole.STUDENT

                student, created = User.objects.get_or_create(
                    register_number=row["register_number"],
                    defaults={
                        "full_name": row["full_name"],
                        "email": row["email"],
                        "department": department,
                        "role": role,
                        "gender": gender,
                    }
                )

                # Update gender if missing
                if not created and not student.gender and gender:
                    student.gender = gender
                    student.save()

                # Track redirect priority
                if role == UserRole.FACULTY_COORDINATOR:
                    redirect_role = UserRole.FACULTY_COORDINATOR
                elif role == UserRole.STUDENT_COORDINATOR and redirect_role != UserRole.FACULTY_COORDINATOR:
                    redirect_role = UserRole.STUDENT_COORDINATOR

            # 🔀 FINAL REDIRECT
            if redirect_role == UserRole.FACULTY_COORDINATOR:
                return redirect("accounts:faculty_dashboard")
            elif redirect_role == UserRole.STUDENT_COORDINATOR:
                return redirect("accounts:student_coordinator_dashboard")

            return redirect("accounts:student_list")

    else:
        form = StudentBulkUploadForm()

    return render(
        request,
        "accounts/student_bulk_upload.html",
        {"form": form},
    )






@login_required
def student_search(request):
    if not is_admin_or_coordinator(request.user):
        return HttpResponseForbidden("Not allowed")

    query = request.GET.get("q", "")
    
    dept = get_user_department(request.user)
    students = User.objects.filter(role=UserRole.STUDENT)
    
    if dept:
        students = students.filter(department=dept)

    students = students.filter(
        Q(full_name__icontains=query) |
        Q(register_number__icontains=query)
    )

    return render(
        request,
        "accounts/student_search.html",
        {
            "students": students,
            "query": query,
        }
    )

    

    
    
@login_required
def student_list(request):
    if not is_admin_or_coordinator(request.user):
        return HttpResponseForbidden("Not allowed")
    
    dept = get_user_department(request.user)
    students = User.objects.filter(role=UserRole.STUDENT)
    
    if dept:
        students = students.filter(department=dept)

    return render(
        request,
        "accounts/student_list.html",
        {"students": students},
    )



@login_required
def add_student_to_event(request, meet_event_id):
    if not is_admin_or_coordinator(request.user):
        return HttpResponseForbidden("Not allowed")

    meet_event = get_object_or_404(MeetEvent, id=meet_event_id)
    event = meet_event.event
    query = request.GET.get("q", "")
    students = []
    
    dept = get_user_department(request.user)

    if query:
        students = User.objects.filter(role=UserRole.STUDENT)
        
        if dept:
            students = students.filter(department=dept)
            
        students = students.filter(
            Q(full_name__icontains=query) |
            Q(register_number__icontains=query)
        )

    manual_form = ManualStudentAddForm()

    return render(
        request,
        "accounts/add_student_to_event.html",
        {
            "meet_event": meet_event,
            "event": event,
            "students": students,
            "query": query,
            "manual_form": manual_form,
        }
    )

@login_required
def register_existing_student(request, meet_event_id, student_id):
    if not is_admin_or_coordinator(request.user):
        return HttpResponseForbidden("Not allowed")
    

    meet_event = get_object_or_404(MeetEvent, id=meet_event_id)
    event = meet_event.event

    if event.status != "ACTIVE":
        return HttpResponseForbidden("Event is not active")

    student = get_object_or_404(User, id=student_id, role=UserRole.STUDENT)
    
    if request.user.role in (
        UserRole.FACULTY_COORDINATOR,
        UserRole.STUDENT_COORDINATOR,
    ):
        if student.department != request.user.department:
            return HttpResponseForbidden("Not Allowed")
        

    Registration.objects.get_or_create(
        meet_event=meet_event,
        participant=student,
    )

    return redirect("accounts:add_student_to_event", meet_event_id=meet_event.id)




@login_required
def add_new_student_and_register(request, meet_event_id):
    if not is_admin_or_coordinator(request.user):
        return HttpResponseForbidden("Not allowed")

    if request.method != "POST":
        return HttpResponseForbidden("Invalid request")

    meet_event = get_object_or_404(MeetEvent, id=meet_event_id)
    event = meet_event.event

    if event.status != "ACTIVE":
        return HttpResponseForbidden("Event is not active")


    form = ManualStudentAddForm(request.POST)
    if form.is_valid():
        student = form.save(commit=False)
        
        if request.user.role in (
            UserRole.FACULTY_COORDINATOR,
            UserRole.STUDENT_COORDINATOR,
        ):
            student.department = request.user.department
            
        student.save()
        
        Registration.objects.get_or_create(
            meet_event=meet_event,
            participant=student,
        )

    return redirect("accounts:add_student_to_event", meet_event_id=meet_event.id)




@login_required
def coordinator_events(request):
    if not is_admin_or_coordinator(request.user):
        return HttpResponseForbidden("Not Allowed")
    
    # Show active meet events
    meet_events = MeetEvent.objects.filter(meet__status=MeetStatus.ACTIVE, is_active=True).select_related('event', 'meet')
    
    return render(request, "accounts/coordinator_events.html", {"meet_events": meet_events})



@login_required
def event_student_report(request):
    if not is_admin_or_coordinator(request.user):
        return HttpResponseForbidden("Not allowed")

    query = request.GET.get("q", "").lower()

    meet_events = MeetEvent.objects.filter(
        meet__status=MeetStatus.ACTIVE
    ).select_related('event', 'meet').prefetch_related(
        "registrations__participant"
    )

    result = []

    for me in meet_events:
        regs = me.registrations.all()

        if query:
            regs = [
                r for r in regs
                if query in (r.participant.full_name or "").lower()
                or query in (r.participant.register_number or "").lower()
            ]


        if regs:
            result.append({
                "meet_event": me,
                "event": me.event,
                "registrations": regs,
            })

    return render(
        request,
        "accounts/event_student_report.html",
        {
            "events": result,
            "query": query,
        }
    )




@login_required
def student_event_register(request, meet_event_id):
    if request.user.role != UserRole.STUDENT:
        return HttpResponseForbidden("Access Denied")

    meet_event = get_object_or_404(MeetEvent, id=meet_event_id)
    event = meet_event.event

    if event.status != "ACTIVE":
        return HttpResponseForbidden("Event is not active")

    if request.user.gender == "MALE" and not event.gender_boys:
        return HttpResponseForbidden("Not allowed")

    if request.user.gender == "FEMALE" and not event.gender_girls:
        return HttpResponseForbidden("Not allowed")

    Registration.objects.get_or_create(
        meet_event=meet_event,
        participant=request.user,
    )

    return redirect("accounts:student_dashboard")




#-------------------------
#   Dashboards
#-------------------------


@login_required
def faculty_coordinator_dashboard(request):
    if request.user.role != UserRole.FACULTY_COORDINATOR:
        return HttpResponseForbidden("Access denied")

    meets = Meet.objects.filter(status=MeetStatus.ACTIVE)

    return render(
        request,
        "accounts/dashboards/faculty_coordinator_dashboard.html",
        {
            "meets": meets,
        }
    )



@login_required
def student_coordinator_dashboard(request):
    if request.user.role != UserRole.STUDENT_COORDINATOR:
        return HttpResponseForbidden("Not Allowed")
    
    department = request.user.department
    
    return render(request, "accounts/dashboards/student_coordinator_dashboard.html", {"department": department})




@login_required
def student_dashboard(request):
    if request.user.role != UserRole.STUDENT:
        return HttpResponseForbidden("Not allowed")
    
    #already registered events
    registrations = Registration.objects.filter(participant=request.user).select_related("event", "event__meet")
    
    registered_event_ids = registrations.values_list("event_id", flat=True)
    
    if request.user.gender == "MALE":
        q_gender = Q(event__gender_boys=True)
    else:
        q_gender = Q(event__gender_girls=True)
        
    available_events = MeetEvent.objects.filter(
        meet__status=MeetStatus.ACTIVE, 
        is_active=True,
        event__status=EventStatus.ACTIVE
    ).filter(q_gender).exclude(id__in=registered_event_ids).select_related("meet", "event")
    
    
    return render(request, "accounts/dashboards/student_dashboard.html", {
            "student": request.user,
            "registrations": registrations,
            "available_events": available_events
        }
    )
    


@login_required
def admin_meet_event_assign(request, meet_id):
    meet = get_object_or_404(Meet, id=meet_id)

    events = Event.objects.filter(status="ACTIVE")

    if request.method == "POST":
        selected_event_ids = request.POST.getlist("events")

        for event_id in selected_event_ids:
            MeetEvent.objects.get_or_create(
                meet=meet,
                event_id=event_id
            )

        return redirect("admin_meet_dashboard")

    return render(request, "admin/assign_events.html", {
        "meet": meet,
        "events": events
    })




@login_required
def faculty_assign_events_to_meet(request, meet_id):
    if request.user.role != UserRole.FACULTY_COORDINATOR:
        return HttpResponseForbidden("Access denied")

    meet = get_object_or_404(Meet, id=meet_id, status=MeetStatus.ACTIVE)

    events = Event.objects.filter(status=EventStatus.ACTIVE)

    if request.method == "POST":
        selected_event_ids = request.POST.getlist("events")

        for event_id in selected_event_ids:
            MeetEvent.objects.get_or_create(
                meet=meet,
                event_id=event_id
            )

        return redirect("accounts:faculty_coordinator_dashboard")

    assigned_event_ids = MeetEvent.objects.filter(
        meet=meet
    ).values_list("event_id", flat=True)

    return render(
        request,
        "accounts/faculty/assign_events.html",
        {
            "meet": meet,
            "events": events,
            "assigned_event_ids": assigned_event_ids,
        }
    )




#-------------------------
#   Login and Logout
#-------------------------

def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:home")

    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]

        student = User.objects.filter(
            email=email,
            role=UserRole.STUDENT
        ).first()

        if student and not student.has_usable_password():
            if student.register_number:
                student.set_password(student.register_number)
                student.save()

        user = authenticate(request, email=email, password=password)

        if user and user.is_active:
            login(request, user)

            if user.role == UserRole.ADMIN:
                return redirect("/admin/")
            elif user.role == UserRole.FACULTY_COORDINATOR:
                return redirect("accounts:faculty_coordinator_dashboard")
            elif user.role == UserRole.STUDENT_COORDINATOR:
                return redirect("accounts:student_coordinator_dashboard")
            else:
                return redirect("accounts:student_dashboard")

        
        form.add_error(None, "Invalid email or password")

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect('accounts:login')