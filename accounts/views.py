import io
from fpdf import FPDF
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponseForbidden, FileResponse
from django.db.models import Q
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import User, Department, UserRole
from accounts.models import Student
from .forms import LoginForm
from meet.models import (
    Event, EventStatus, EventType,
    Meet, MeetEvent, MeetStatus,
    Registration, Team, TeamMember
)





# =====================================================
# Helpers
# =====================================================

def is_admin_or_coordinator_or_faculty(user):
    return user.role in (
        UserRole.ADMIN,
        UserRole.FACULTY_COORDINATOR,
        UserRole.STUDENT_COORDINATOR,
        UserRole.FACULTY,
    )


def is_admin_or_coordinator(user):
    return user.role in (
        UserRole.ADMIN,
        UserRole.FACULTY_COORDINATOR,
        UserRole.STUDENT_COORDINATOR,
    )


def get_user_department(user):
    if user.role in (
        UserRole.FACULTY_COORDINATOR,
        UserRole.STUDENT_COORDINATOR,
        UserRole.FACULTY,
    ):
        return user.department
    return None





@login_required
def home(request):
    return render(request, "accounts/home.html")




# =====================================================
# Public (NO STUDENT LOGIN)
# =====================================================

def public_home(request):
    active_meet = Meet.objects.filter(status=MeetStatus.ACTIVE).first()

    meet_events = MeetEvent.objects.filter(
        meet=active_meet,
        is_active=True,
        event__status=EventStatus.ACTIVE
    ).select_related("event").prefetch_related("teams__teammember_set")

    return render(request, "public/home.html", {
        "meet_events": meet_events,
        "departments": Department.objects.all(),
        "semesters": ["S1", "S2", "S3", "S4", "S5", "S6"],
    })


def student_register(request):
    if request.method != "POST":
        return redirect("accounts:public_home")

    student, _ = Student.objects.get_or_create(
        register_number=request.POST["register_number"],
        defaults={
            "full_name": request.POST["full_name"],
            "gender": request.POST["gender"],
            "department_id": request.POST["department"],
            "semester": request.POST["semester"],
        }
    )

    # Clear ACTIVE meet data only
    Registration.objects.filter(
        participant=student,
        meet_event__meet__status=MeetStatus.ACTIVE
    ).delete()

    TeamMember.objects.filter(
        student=student,
        team__meet_event__meet__status=MeetStatus.ACTIVE
    ).delete()

    with transaction.atomic():

        # Individual events
        for me in MeetEvent.objects.filter(
            id__in=request.POST.getlist("events"),
            event__event_type=EventType.INDIVIDUAL,
            meet__status=MeetStatus.ACTIVE
        ):
            Registration.objects.create(
                meet_event=me,
                participant=student
            )

        # Team events
        for me in MeetEvent.objects.filter(
            id__in=request.POST.getlist("team_events"),
            event__event_type=EventType.TEAM,
            meet__status=MeetStatus.ACTIVE
        ):
            team, _ = Team.objects.get_or_create(
                meet_event=me,
                department=student.department
            )

            if team.teammember_set.count() >= me.event.max_team_size:
                messages.error(
                    request,
                    f"{student.department.name} team is full for {me.event.name}"
                )
                continue

            TeamMember.objects.create(
                team=team,
                student=student
            )

    messages.success(request, "Registration successful!")
    return redirect("accounts:public_home")


    




# =====================================================
# Student Views (ADMIN/FACULTY ONLY)
# =====================================================

@login_required
def student_search(request):
    if not is_admin_or_coordinator_or_faculty(request.user):
        return HttpResponseForbidden()

    query = request.GET.get("q", "")

    students = Student.objects.filter(
        Q(registration__meet_event__meet__status=MeetStatus.ACTIVE) |
        Q(teammember__team__meet_event__meet__status=MeetStatus.ACTIVE)
    ).select_related("department").distinct()

    if query:
        students = students.filter(
            Q(full_name__icontains=query) |
            Q(register_number__icontains=query)
        )

    return render(request, "accounts/student_search.html", {
        "students": students,
        "query": query,
    })





@login_required
def student_list(request):
    if not is_admin_or_coordinator_or_faculty(request.user):
        return HttpResponseForbidden()

    students = Student.objects.filter(
        Q(registration__meet_event__meet__status=MeetStatus.ACTIVE) |
        Q(teammember__team__meet_event__meet__status=MeetStatus.ACTIVE)
    ).select_related("department").distinct()

    return render(request, "accounts/student_list.html", {
        "students": students
    })






@login_required
def event_students(request, meet_event_id):
    if not is_admin_or_coordinator_or_faculty(request.user):
        return HttpResponseForbidden()

    meet_event = get_object_or_404(MeetEvent, id=meet_event_id)
    dept = get_user_department(request.user)

    boys, girls = [], []

    if meet_event.event.event_type == EventType.INDIVIDUAL:
        qs = Registration.objects.filter(meet_event=meet_event)
        if dept:
            qs = qs.filter(participant__department=dept)

        for r in qs:
            (boys if r.participant.gender == "MALE" else girls).append(r.participant)

    else:
        qs = TeamMember.objects.filter(team__meet_event=meet_event)
        if dept:
            qs = qs.filter(student__department=dept)

        for tm in qs:
            (boys if tm.student.gender == "MALE" else girls).append(tm.student)

    return render(request, "accounts/event_students.html", {
        "meet_event": meet_event,
        "boys": boys,
        "girls": girls,
    })









@login_required
def export_registered_students_pdf(request, meet_event_id):
    meet_event = get_object_or_404(MeetEvent, id=meet_event_id)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 15)
    pdf.cell(0, 10, f'Registered Students - {meet_event.event.name}', ln=True, align='C')
    pdf.ln(8)

    pdf.set_font('helvetica', 'B', 10)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(60, 10, 'Name', 1, 0, 'C', True)
    pdf.cell(40, 10, 'Register No', 1, 0, 'C', True)
    pdf.cell(50, 10, 'Department', 1, 0, 'C', True)
    pdf.cell(30, 10, 'Gender', 1, 1, 'C', True)

    pdf.set_font('helvetica', '', 10)

    if meet_event.event.event_type == EventType.INDIVIDUAL:
        data = Registration.objects.filter(
            meet_event=meet_event
        ).select_related("participant", "participant__department")

        for r in data:
            s = r.participant
            pdf.cell(60, 8, s.full_name[:30], 1)
            pdf.cell(40, 8, s.register_number, 1)
            pdf.cell(50, 8, s.department.name if s.department else "-", 1)
            pdf.cell(30, 8, s.get_gender_display(), 1)
            pdf.ln()

    else:
        members = TeamMember.objects.filter(
            team__meet_event=meet_event
        ).select_related("student", "student__department")

        for m in members:
            s = m.student
            pdf.cell(60, 8, s.full_name[:30], 1)
            pdf.cell(40, 8, s.register_number, 1)
            pdf.cell(50, 8, s.department.name if s.department else "-", 1)
            pdf.cell(30, 8, s.get_gender_display(), 1)
            pdf.ln()

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)

    return FileResponse(
        buf,
        as_attachment=True,
        filename=f"{meet_event.event.name}_registrations.pdf"
    )









@login_required
def coordinator_events(request):
    if not is_admin_or_coordinator(request.user):
        return HttpResponseForbidden("Not Allowed")
    
    meet_events = (
        MeetEvent.objects
        .filter(
            meet__status=MeetStatus.ACTIVE,
            is_active=True
        )
        .select_related("event", "meet")
        .prefetch_related(
            "registrations__participant",
            "teams__teammember_set__student"
        )
    )
    
    return render(
        request,
        "accounts/coordinator_events.html",
        {
            "meet_events": meet_events
        }
    )



@login_required
def event_student_report(request):
    if not is_admin_or_coordinator_or_faculty(request.user):
        return HttpResponseForbidden("Not allowed")

    result = []

    meet_events = MeetEvent.objects.filter(
        meet__status=MeetStatus.ACTIVE,
        is_active=True
    ).select_related("event", "meet")

    for me in meet_events:
        boys, girls = [], []

        if me.event.event_type == EventType.INDIVIDUAL:
            regs = me.registrations.select_related("participant")
            for r in regs:
                (boys if r.participant.gender == "MALE" else girls).append(r.participant)

        else:
            members = TeamMember.objects.filter(
                team__meet_event=me
            ).select_related("student")
            for m in members:
                (boys if m.student.gender == "MALE" else girls).append(m.student)

        if boys or girls:
            result.append({
                "meet_event": me,
                "boys": boys,
                "girls": girls
            })

    return render(request, "accounts/event_student_report.html", {
        "events": result
    })










@login_required
def download_event_report_pdf(request, meet_event_id, gender=None):
    if not is_admin_or_coordinator_or_faculty(request.user):
        return HttpResponseForbidden("Not allowed")

    meet_event = get_object_or_404(MeetEvent, id=meet_event_id)

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, f"Event Report: {meet_event.event.name}", ln=True, align="C")
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 10, f"Meet: {meet_event.meet.name}", ln=True, align="C")
    pdf.ln(8)

    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(50, 8, "Name", 1, 0, "C", True)
    pdf.cell(35, 8, "Register No", 1, 0, "C", True)
    pdf.cell(55, 8, "Department", 1, 0, "C", True)
    pdf.cell(30, 8, "Gender", 1, 1, "C", True)

    pdf.set_font("helvetica", "", 10)

    # -------------------------
    # INDIVIDUAL EVENTS
    # -------------------------
    if meet_event.event.event_type == EventType.INDIVIDUAL:
        data = Registration.objects.filter(
            meet_event=meet_event
        ).select_related("participant", "participant__department")

        for r in data:
            s = r.participant
            pdf.cell(50, 8, s.full_name[:25], 1)
            pdf.cell(35, 8, s.register_number, 1)
            pdf.cell(55, 8, s.department.name if s.department else "-", 1)
            pdf.cell(30, 8, s.get_gender_display(), 1)
            pdf.ln()

    # -------------------------
    # TEAM EVENTS
    # -------------------------
    else:
        members = TeamMember.objects.filter(
            team__meet_event=meet_event
        ).select_related("student", "student__department")

        for m in members:
            s = m.student
            pdf.cell(50, 8, s.full_name[:25], 1)
            pdf.cell(35, 8, s.register_number, 1)
            pdf.cell(55, 8, s.department.name if s.department else "-", 1)
            pdf.cell(30, 8, s.get_gender_display(), 1)
            pdf.ln()

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)

    return FileResponse(
        buf,
        as_attachment=True,
        filename=f"{meet_event.event.name}_report.pdf"
    )






#-------------------------
#   Dashboards
#-------------------------


@login_required
def faculty_coordinator_dashboard(request):
    if request.user.role != UserRole.FACULTY_COORDINATOR:
        return HttpResponseForbidden("Access denied")

    meets = Meet.objects.filter(status=MeetStatus.ACTIVE).order_by("-id")
    
    meets_data = []
    for meet in meets:
        assigned_events = MeetEvent.objects.filter(
            meet=meet,
            is_active=True
        ).select_related('event')
        
        meets_data.append({
            "meet": meet,
            "assigned_events": assigned_events
        })

    department = request.user.department

    return render(
        request,
        "accounts/dashboards/faculty_coordinator_dashboard.html",
        {
            "meets_data": meets_data,
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
def admin_dashboard(request):
    if request.user.role != UserRole.ADMIN:
        return HttpResponseForbidden("Access denied")

    meets = Meet.objects.all().order_by("-id")

    meets_data = []
    for meet in meets:
        assigned_events = MeetEvent.objects.filter(
            meet=meet,
            is_active=True
        ).select_related("event")

        meets_data.append({
            "meet": meet,
            "assigned_events": assigned_events
        })

    return render(
        request,
        "accounts/admin/dashboard.html",
        {
            "meets_data": meets_data
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
        return HttpResponseForbidden()

    if request.method == "POST":
        try:
            max_team_size = request.POST.get("max_team_size")
            
            Event.objects.create(
                name=request.POST.get("name"),
                category=request.POST.get("category"),
                event_type=request.POST.get("event_type"),
                max_team_size=int(max_team_size) if max_team_size else None,
                status=request.POST.get("status"),
            )
            messages.success(request, "Event created successfully")
            return redirect("accounts:admin_dashboard")

        except ValidationError as e:
            # 👇 THIS IS THE FIX
            for msg in e.messages:
                messages.error(request, msg)

    return render(request, "accounts/admin/create_event.html")






@login_required
def faculty_assign_events_to_meet(request, meet_id):
    if request.user.role != UserRole.FACULTY_COORDINATOR:
        return HttpResponseForbidden()

    meet = get_object_or_404(Meet, id=meet_id, status=MeetStatus.ACTIVE)
    events = Event.objects.filter(status=EventStatus.ACTIVE)

    assigned_event_ids = MeetEvent.objects.filter(
        meet=meet,
        is_active=True
    ).values_list("event_id", flat=True)

    if request.method == "POST":
        selected_event_ids = request.POST.getlist("events")

        MeetEvent.objects.filter(meet=meet).update(is_active=False)

        for event_id in selected_event_ids:
            MeetEvent.objects.update_or_create(
                meet=meet,
                event_id=event_id,
                defaults={"is_active": True}
            )

        return redirect("accounts:faculty_coordinator_dashboard")

    return render(
        request,
        "accounts/assign_events.html",
        {
            "meet": meet,
            "events": events,
            "assigned_event_ids": assigned_event_ids,
        }
    )









@login_required
def team_events_manage(request):
    if request.user.role != UserRole.FACULTY_COORDINATOR:
        return HttpResponseForbidden("Access denied")

    meet_events = MeetEvent.objects.filter(
        event__event_type=EventType.TEAM,
        meet__status=MeetStatus.ACTIVE,
        is_active=True
    ).select_related("event", "meet").prefetch_related("teams")

    return render(
        request,
        "accounts/team_events_manage.html",
        {
            "meet_events": meet_events
        }
    )




# =====================================================
# AUTH (STAFF ONLY)
# =====================================================

def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:home")

    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]

        user = authenticate(request, email=email, password=password)

        if user is not None and user.is_active:
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
                return redirect("accounts:public_home")

        form.add_error(None, "Invalid email or password")

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("accounts:login")






@login_required
def results_dashboard(request):
    if not is_admin_or_coordinator(request.user):
        return HttpResponseForbidden("Not allowed")
    
    active_meets = Meet.objects.filter(status=MeetStatus.ACTIVE).prefetch_related('meetevent_set__event')
    return render(request, "accounts/results_dashboard.html", {"active_meets": active_meets})






# =====================================================
# RESULTS (LOGIC PRESERVED)
# =====================================================

@login_required
def manage_event_results(request, meet_event_id):
    if not is_admin_or_coordinator(request.user):
        return HttpResponseForbidden()

    meet_event = get_object_or_404(MeetEvent, id=meet_event_id)

    if meet_event.event.event_type == EventType.TEAM:
        return HttpResponseForbidden("Team event results not allowed")

    query = request.GET.get("q", "").strip()

    students = Student.objects.filter(
        registration__meet_event=meet_event
    ).select_related("department")

    if query:
        students = students.filter(
            Q(full_name__icontains=query) |
            Q(register_number__icontains=query)
        )

    regs = Registration.objects.filter(meet_event=meet_event)
    reg_map = {r.participant_id: r for r in regs}

    for s in students:
        s.reg = reg_map.get(s.id)

    return render(request, "accounts/manage_results.html", {
        "meet_event": meet_event,
        "students": students,
        "query": query,   # ✅ REQUIRED
    })






@login_required
def set_registration_position(request, meet_event_id, student_id):
    if not is_admin_or_coordinator(request.user):
        return HttpResponseForbidden()

    meet_event = get_object_or_404(MeetEvent, id=meet_event_id)
    student = get_object_or_404(Student, id=student_id)

    registration = Registration.objects.get(
        meet_event=meet_event,
        participant=student
    )

    position = request.POST.get("position")
    registration.position = int(position) if position else None
    registration.save()

    messages.success(request, "Position updated")
    return redirect("accounts:manage_event_results", meet_event_id=meet_event.id)







@login_required
def export_results_pdf(request, meet_event_id):
    meet_event = get_object_or_404(MeetEvent, id=meet_event_id)

    winners = Registration.objects.filter(
        meet_event=meet_event,
        position__isnull=False
    ).order_by("position")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, meet_event.event.name, ln=True, align="C")

    pdf.set_font("helvetica", "", 10)

    for r in winners:
        pdf.cell(
            0, 8,
            f"{r.position}. {r.participant.full_name} ({r.participant.register_number})",
            ln=True
        )

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)

    return FileResponse(buf, as_attachment=True, filename="results.pdf")