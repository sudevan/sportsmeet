import csv
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.http import HttpResponseForbidden
from django.db.models import Q

from .models import User, Department, UserRole
from .forms import StudentBulkUploadForm, ManualStudentAddForm, LoginForm
from meet.models import Event, EventStatus, EventType, Meet, MeetEvent, MeetStatus, Registration, Team, TeamMember




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

    if request.user.gender == "MALE" and not meet_event.gender_boys:
        return HttpResponseForbidden("Not allowed")

    if request.user.gender == "FEMALE" and not meet_event.gender_girls:
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

    meets = Meet.objects.filter(status=MeetStatus.ACTIVE).order_by("-id")
    department = request.user.department

    return render(
        request,
        "accounts/dashboards/faculty_coordinator_dashboard.html",
        {
            "meets": meets,
            "department": department,
        }
    )


@login_required
def faculty_dashboard(request):
    if request.user.role != UserRole.FACULTY:
        return HttpResponseForbidden("Access denied")

    meets = Meet.objects.all().order_by("-id")
    department = request.user.department

    return render(
        request,
        "accounts/dashboards/faculty_dashboard.html",
        {
            "meets": meets,
            "department": department,
        }
    )


@login_required
def student_coordinator_dashboard(request):
    if request.user.role != UserRole.STUDENT_COORDINATOR:
        return HttpResponseForbidden("Not Allowed")
    
    department = request.user.department
    meets = Meet.objects.filter(status=MeetStatus.ACTIVE).order_by("-id")
    
    return render(
        request, 
        "accounts/dashboards/student_coordinator_dashboard.html", 
        {
            "department": department,
            "meets": meets,
        }
    )




@login_required
def student_dashboard(request):
    if request.user.role != UserRole.STUDENT:
        return HttpResponseForbidden("Not allowed")
    
    # already registered events
    registrations = Registration.objects.filter(participant=request.user).select_related(
        "meet_event", "meet_event__event", "meet_event__meet"
    )
    
    registered_meet_event_ids = registrations.values_list("meet_event_id", flat=True)
    
    if request.user.gender == "MALE":
        q_gender = Q(gender_boys=True)
    else:
        q_gender = Q(gender_girls=True)

        
    available_events = MeetEvent.objects.filter(
        meet__status=MeetStatus.ACTIVE, 
        is_active=True,
        event__status=EventStatus.ACTIVE
    ).filter(q_gender).exclude(id__in=registered_meet_event_ids).select_related("meet", "event")
    
    return render(request, "accounts/dashboards/student_dashboard.html", {
            "student": request.user,
            "registrations": registrations,
            "available_events": available_events
        }
    )
    
    
    
@login_required
def admin_dashboard(request):
    if request.user.role != UserRole.ADMIN:
        return HttpResponseForbidden("Access denied")

    meets = Meet.objects.all().order_by("-id")

    return render(
        request,
        "accounts/admin/dashboard.html",
        {
            "meets": meets
        }
    )
    




@login_required
def admin_meet_event_assign(request, meet_id):
    if request.user.role != UserRole.ADMIN:
        return HttpResponseForbidden("Access Denied!!!")

    meet = get_object_or_404(Meet, id=meet_id)
    events = Event.objects.filter(status="ACTIVE")

    assigned_meet_events = MeetEvent.objects.filter(meet=meet)
    assigned_event_ids = assigned_meet_events.filter(
        is_active=True
    ).values_list("event_id", flat=True)

    if request.method == "POST":
        selected_event_ids = set(map(int, request.POST.getlist("events")))

        for event in events:
            meet_event, created = MeetEvent.objects.get_or_create(
                meet=meet,
                event=event
            )

            # ✅ toggle active/inactive
            meet_event.is_active = event.id in selected_event_ids
            meet_event.save()

        return redirect("accounts:admin_dashboard")

    return render(
        request,
        "accounts/admin/assign_events.html",
        {
            "meet": meet,
            "events": events,
            "assigned_event_ids": assigned_event_ids,
        }
    )






@login_required
def admin_create_meet(request):
    if request.user.role != UserRole.ADMIN:
        return HttpResponseForbidden("Access Denied!!!")
    
    if request.method == "POST":
        Meet.objects.create(
            name = request.POST["name"],
            start_date = request.POST["start_date"],
            end_date = request.POST["end_date"],
            status = request.POST["status"]
        )
        return redirect("accounts:admin_dashboard")
    
    return render(request, "accounts/admin/create_meet.html")





@login_required
def admin_create_event(request):
    if request.user.role != UserRole.ADMIN:
        return HttpResponseForbidden("Access denied")

    if request.method == "POST":
        Event.objects.create(
            name=request.POST["name"],
            category=request.POST["category"],
            event_type=request.POST["event_type"],
            status=request.POST["status"]
        )
        return redirect("accounts:admin_dashboard")

    return render(request, "accounts/admin/create_event.html")





@login_required
def faculty_assign_events_to_meet(request, meet_id):
    if request.user.role != UserRole.FACULTY_COORDINATOR:
        return HttpResponseForbidden("Access denied")

    meet = get_object_or_404(Meet, id=meet_id, status=MeetStatus.ACTIVE)
    events = Event.objects.filter(status=EventStatus.ACTIVE)

    assigned_meet_events = MeetEvent.objects.filter(meet=meet)

    assigned_event_ids = assigned_meet_events.filter(
        is_active=True
    ).values_list("event_id", flat=True)

    assigned_boys_event_ids = assigned_meet_events.filter(
        gender_boys=True
    ).values_list("event_id", flat=True)

    assigned_girls_event_ids = assigned_meet_events.filter(
        gender_girls=True
    ).values_list("event_id", flat=True)

    if request.method == "POST":
        selected_event_ids = request.POST.getlist("events")

        for event in events.filter(id__in=selected_event_ids):

            boys = request.POST.get(f"boys_{event.id}") == "on"
            girls = request.POST.get(f"girls_{event.id}") == "on"

            if not boys and not girls:
                messages.error(
                    request,
                    f"Select at least one gender for {event.name}"
                )
                return redirect(request.path)

            min_size = request.POST.get(f"min_{event.id}")
            max_size = request.POST.get(f"max_{event.id}")

            if event.event_type == EventType.TEAM:
                if not min_size or not max_size:
                    messages.error(
                        request,
                        f"Set team strength for {event.name}"
                    )
                    return redirect(request.path)

                min_size = int(min_size)
                max_size = int(max_size)
            else:
                min_size = None
                max_size = None

        
            meet_event = MeetEvent.objects.filter(
                meet=meet,
                event=event
            ).first()

            if not meet_event:
                meet_event = MeetEvent(
                    meet=meet,
                    event=event
                )

            meet_event.gender_boys = boys
            meet_event.gender_girls = girls
            meet_event.min_team_size = min_size
            meet_event.max_team_size = max_size
            meet_event.is_active = True

            meet_event.save()

        # deactivate unselected events
        MeetEvent.objects.filter(
            meet=meet
        ).exclude(
            event_id__in=selected_event_ids
        ).update(is_active=False)

        return redirect("accounts:faculty_coordinator_dashboard")

    return render(
        request,
        "accounts/assign_events.html",
        {
            "meet": meet,
            "events": events,
            "assigned_event_ids": assigned_event_ids,
            "assigned_boys_event_ids": assigned_boys_event_ids,
            "assigned_girls_event_ids": assigned_girls_event_ids,
        }
    )





@login_required
def create_team(request, meet_event_id):
    if request.user.role not in (
        UserRole.ADMIN,
        UserRole.FACULTY_COORDINATOR,
    ):
        return HttpResponseForbidden("Not allowed")
    
    # if request.user.role == UserRole.FACULTY_COORDINATOR:
    #     if meet_event.meet.department != request.user.department:
    #         return HttpResponseForbidden("Not your department")


    meet_event = get_object_or_404(
        MeetEvent,
        id=meet_event_id,
        event__event_type=EventType.TEAM,
        is_active=True,
    )

    if request.method == "POST":
        name = request.POST.get("name")

        if not name:
            messages.error(request, "Team name required")
            return redirect(request.path)

        Team.objects.create(
            meet_event=meet_event,
            name=name,
            created_by=request.user
        )

        messages.success(request, "Team created")
        return redirect(
            "accounts:manage_team_members",
            team_id=Team.objects.latest("id").id
        )

    return render(
        request,
        "accounts/team/create_team.html",
        {"meet_event": meet_event}
    )





@login_required
def manage_team_members(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    meet_event = team.meet_event

    if request.user.role not in (
        UserRole.ADMIN,
        UserRole.FACULTY_COORDINATOR,
    ):
        return HttpResponseForbidden("Not allowed")

    students = User.objects.filter(
        role=UserRole.STUDENT,
        gender__in=[
            "MALE" if meet_event.gender_boys else "",
            "FEMALE" if meet_event.gender_girls else "",
        ]
    )

    members = TeamMember.objects.filter(team=team)

    if request.method == "POST":
        student_id = request.POST.get("student")

        student = get_object_or_404(User, id=student_id)

        TeamMember.objects.get_or_create(
            team=team,
            student=student
        )

        messages.success(request, "Student added")
        return redirect(request.path)

    return render(
        request,
        "accounts/team/manage_members.html",
        {
            "team": team,
            "students": students,
            "members": members,
        }
    )





@login_required
def set_team_captain(request, team_id, member_id):
    team = get_object_or_404(Team, id=team_id)

    if request.user.role not in (
        UserRole.ADMIN,
        UserRole.FACULTY_COORDINATOR,
    ):
        return HttpResponseForbidden("Not allowed")

    TeamMember.objects.filter(
        team=team,
        is_captain=True
    ).update(is_captain=False)

    member = get_object_or_404(
        TeamMember,
        id=member_id,
        team=team
    )
    member.is_captain = True
    member.save()

    messages.success(request, "Captain assigned")
    return redirect(
        "accounts:manage_team_members",
        team_id=team.id
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
            elif user.role == UserRole.FACULTY:
                return redirect("accounts:faculty_dashboard")
            elif user.role == UserRole.STUDENT_COORDINATOR:
                return redirect("accounts:student_coordinator_dashboard")
            else:
                return redirect("accounts:student_dashboard")

        
        form.add_error(None, "Invalid email or password")

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect('accounts:login')