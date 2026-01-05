import csv
import io
from xml.dom import ValidationErr
from django.core.exceptions import ValidationError
from fpdf import FPDF
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.http import HttpResponseForbidden, HttpResponse, FileResponse
from django.db.models import Q



from .models import User, Department, UserRole, Gender
from .forms import StudentBulkUploadForm, ManualStudentAddForm, LoginForm
from meet.models import Event, EventStatus, EventType, Meet, MeetEvent, MeetStatus, Registration, Team, TeamMember




@login_required
def home(request):
    return render(request, "accounts/home.html")




def is_admin_or_coordinator_or_faculty(user):
    return user.role in [
        UserRole.ADMIN,
        UserRole.FACULTY_COORDINATOR,
        UserRole.STUDENT_COORDINATOR,
        UserRole.FACULTY,
    ]


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
        UserRole.FACULTY,
    ):
        return user.department
    return None

def public_home(request):
    active_meet = Meet.objects.filter(status=MeetStatus.ACTIVE).first()

    meet_events = MeetEvent.objects.filter(
        meet=active_meet,
        is_active=True,
        event__status=EventStatus.ACTIVE
    ).select_related("event")

    return render(request, "public/home.html", {
        "meet_events": meet_events,
        "departments": Department.objects.all(),  # ✅ ADD THIS
        "semesters": range(1, 7),                  # ✅ ADD THIS
    })




"""def student_register(request):
    if request.method == "POST":
        individual_ids = request.POST.getlist("events")
        team_ids = request.POST.getlist("teams")

        if len(individual_ids) > 3:
            messages.error(request, "Max 3 individual events allowed")
            return redirect("home")

        if len(team_ids) > 2:
            messages.error(request, "Max 2 team events allowed")
            return redirect("home")

        user, _ = User.objects.get_or_create(
            register_number=request.POST["register_number"],
            defaults={
                "full_name": request.POST["full_name"],
                "gender": request.POST["gender"],
                "department_id": request.POST["department"],
                "semester": request.POST["semester"], 
                "role": UserRole.STUDENT,
            }
        )

        # Individual registrations
        for me_id in individual_ids:
            Registration.objects.get_or_create(
                meet_event_id=me_id,
                participant=user
            )

        # Team registrations
        for team_id in team_ids:
            team = Team.objects.get(id=team_id)
            event = team.meet_event.event

            if team.teammember_set.count() >= event.max_team_size:
                messages.error(
                    request,
                    f"Team '{team.name}' is full"
                )
                continue

            TeamMember.objects.get_or_create(
                team=team,
                student=user
            )


        messages.success(request, "Registration successful!")
        return redirect("home")"""
def student_register(request):
    if request.method == "POST":
        required_fields = [
            "full_name", "register_number",
            "gender", "department", "semester"
        ]
        for field in required_fields:
            if not request.POST.get(field):
                messages.error(request, "All fields are required.")
                return redirect("accounts:public_home")

        individual_ids = request.POST.getlist("events")
        team_ids = request.POST.getlist("teams")

        if len(individual_ids) > 3:
            messages.error(request, "Maximum 3 individual events allowed.")
            return redirect("accounts:public_home")

        if len(team_ids) > 2:
            messages.error(request, "Maximum 2 team events allowed.")
            return redirect("accounts:public_home")

        semester = int(request.POST["semester"])

        user, created = User.objects.get_or_create(
            register_number=request.POST["register_number"],
            defaults={
                "full_name": request.POST["full_name"],
                "gender": request.POST["gender"],
                "department_id": request.POST["department"],
                "semester": semester,
                "role": UserRole.STUDENT,
            }
        )

        if not created:
            user.full_name = request.POST["full_name"]
            user.gender = request.POST["gender"]
            user.department_id = request.POST["department"]
            user.semester = semester
            user.save()

            Registration.objects.filter(participant=user).delete()
            TeamMember.objects.filter(student=user).delete()

        with transaction.atomic():
            for me_id in individual_ids:
                Registration.objects.create(
                    meet_event_id=me_id,
                    participant=user
                )

            for team_id in team_ids:
                team = get_object_or_404(Team, id=team_id)
                max_size = team.meet_event.event.max_team_size
                if TeamMember.objects.filter(team=team).count() >= max_size:
                    messages.error(
                        request,
                        f"Team '{team.name}' is full."
                    )
                    continue

                TeamMember.objects.create(
                    team=team,
                    student=user
                )

        messages.success(request, "Registration successful!")
        return redirect("accounts:public_home")

@login_required
def student_search(request):
    if not is_admin_or_coordinator_or_faculty(request.user):
        return HttpResponseForbidden("Not allowed")

    query = request.GET.get("q", "")
    
    dept = get_user_department(request.user)
    students = User.objects.filter(
        role__in=[UserRole.STUDENT, UserRole.STUDENT_COORDINATOR]
    )
    
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
    if not is_admin_or_coordinator_or_faculty(request.user):
        return HttpResponseForbidden("Not allowed")
    
    dept = get_user_department(request.user)
    students = User.objects.filter(
        role__in=[UserRole.STUDENT, UserRole.STUDENT_COORDINATOR]
    )
    
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

    # --- HANDLE BULK ADD (POST) ---
    if request.method == "POST":
        student_ids = request.POST.getlist("student_ids")
        if student_ids:
            students_to_add = User.objects.filter(id__in=student_ids, role=UserRole.STUDENT)
            
            # optional: verify department access
            if request.user.role in (UserRole.FACULTY_COORDINATOR, UserRole.STUDENT_COORDINATOR):
                students_to_add = students_to_add.filter(department=request.user.department)

            added_count = 0
            newly_added_ids = []
            for student in students_to_add:
                try:
                    _, created = Registration.objects.get_or_create(meet_event=meet_event, participant=student)
                    if created:
                        added_count += 1
                        newly_added_ids.append(student.id)
                except ValidationErr as e:
                    messages.error(request, f"Error adding {student.full_name}: {e.message_dict.get('__all__', [str(e)])[0]}")
            
            if added_count > 0:
                messages.success(request, f"Added {added_count} students to {event.name}")
                # Store in session for "Recently Added" section
                request.session[f'recently_added_{meet_event.id}'] = newly_added_ids
        
        return redirect("accounts:add_student_to_event", meet_event_id=meet_event.id)

    # --- HANDLE FILTERS (GET) ---
    query = request.GET.get("q", "").strip()
    dept_id = request.GET.get("department")
    semester = request.GET.get("semester")

    students = User.objects.filter(role=UserRole.STUDENT).select_related('department')

    # Role-based restriction: Default to user's department but allow choosing others
    user_dept = get_user_department(request.user)
    
    # Filter Logic
    if dept_id and dept_id.isdigit():
        current_dept_id = int(dept_id)
        students = students.filter(department_id=current_dept_id)
    elif user_dept:
        # Default to user's department if no filter selected
        current_dept_id = user_dept.id
        students = students.filter(department=user_dept)
    else:
        current_dept_id = None
    
    if semester:
        students = students.filter(semester=semester)

    if query:
        students = students.filter(
            Q(full_name__icontains=query) |
            Q(register_number__icontains=query)
        )
    
    # Exclude already registered
    registered_ids = Registration.objects.filter(meet_event=meet_event).values_list("participant_id", flat=True)
    students = students.exclude(id__in=registered_ids).order_by('full_name')
    
    # Registered Students Filters
    reg_dept = request.GET.get('reg_dept')
    reg_gender = request.GET.get('reg_gender')
    reg_q = request.GET.get('reg_q', '')

    registered_registrations = Registration.objects.filter(meet_event=meet_event).select_related('participant', 'participant__department')

    if reg_dept and reg_dept.isdigit():
        registered_registrations = registered_registrations.filter(participant__department_id=int(reg_dept))
    
    if reg_gender:
        registered_registrations = registered_registrations.filter(participant__gender=reg_gender)
    
    if reg_q:
        registered_registrations = registered_registrations.filter(
            Q(participant__full_name__icontains=reg_q) |
            Q(participant__register_number__icontains=reg_q)
        )

    registered_registrations = registered_registrations.order_by('participant__full_name')
    
    # Recently Registered IDs (from session) for highlighting
    recently_added_ids = request.session.get(f'recently_added_{meet_event.id}', [])

    departments = Department.objects.all()
    semesters = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"] 

    manual_form = ManualStudentAddForm()

    return render(
        request,
        "accounts/add_student_to_event.html",
        {
            "meet_event": meet_event,
            "event": event,
            "students": students,
            "registered_registrations": registered_registrations,
            "recently_added_ids": recently_added_ids,
            "query": query,
            "selected_dept": current_dept_id,
            "selected_sem": semester,
            "departments": departments,
            "semesters": semesters,
            "genders": Gender.choices,
            "manual_form": manual_form,
            "reg_dept": int(reg_dept) if (reg_dept and reg_dept.isdigit()) else None,
            "reg_gender": reg_gender,
            "reg_q": reg_q,
        },
    )



@login_required
def export_registered_students_pdf(request, meet_event_id):
    meet_event = get_object_or_404(MeetEvent, id=meet_event_id)
    
    reg_dept = request.GET.get('reg_dept')
    reg_gender = request.GET.get('reg_gender')
    reg_q = request.GET.get('reg_q', '')

    registrations = Registration.objects.filter(meet_event=meet_event).select_related('participant', 'participant__department')

    if reg_dept and reg_dept.isdigit():
        registrations = registrations.filter(participant__department_id=int(reg_dept))
    if reg_gender:
        registrations = registrations.filter(participant__gender=reg_gender)
    if reg_q:
        registrations = registrations.filter(
            Q(participant__full_name__icontains=reg_q) |
            Q(participant__register_number__icontains=reg_q)
        )
    
    registrations = registrations.order_by('participant__full_name')

    

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    pdf.set_font('helvetica', 'B', 15)
    pdf.cell(0, 10, f'Registered Students - {meet_event.event.name}', 0, 1, 'C')
    pdf.ln(5)

    # Table Header
    pdf.set_fill_color(200, 200, 200)
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(60, 10, 'Name', 1, 0, 'C', 1)
    pdf.cell(40, 10, 'Register No', 1, 0, 'C', 1)
    pdf.cell(35, 10, 'Dept', 1, 0, 'C', 1)
    pdf.cell(25, 10, 'Gender', 1, 0, 'C', 1)
    pdf.cell(25, 10, 'Sem', 1, 0, 'C', 1)
    pdf.ln()

    pdf.set_font('helvetica', '', 10)
    for reg in registrations:
        pdf.cell(60, 10, str(reg.participant.full_name)[:30], 1)
        pdf.cell(40, 10, str(reg.participant.register_number), 1)
        pdf.cell(35, 10, str(reg.participant.department.name if reg.participant.department else "-")[:18], 1)
        pdf.cell(25, 10, str(reg.participant.get_gender_display() if reg.participant.gender else "-"), 1)
        pdf.cell(25, 10, str(reg.participant.semester if reg.participant.semester else "-"), 1)
        pdf.ln()

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)

    filename = f"registrations_{meet_event.event.name.replace(' ', '_')}.pdf"
    return FileResponse(buf, as_attachment=True, filename=filename)

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




# @login_required
# def add_new_student_and_register(request, meet_event_id):
#     if not is_admin_or_coordinator(request.user):
#         return HttpResponseForbidden("Not allowed")

#     if request.method != "POST":
#         return HttpResponseForbidden("Invalid request")

#     meet_event = get_object_or_404(MeetEvent, id=meet_event_id)
#     event = meet_event.event

#     if event.status != "ACTIVE":
#         return HttpResponseForbidden("Event is not active")


#     form = ManualStudentAddForm(request.POST)
#     if form.is_valid():
#         student = form.save(commit=False)
        
#         if request.user.role in (
#             UserRole.FACULTY_COORDINATOR,
#             UserRole.STUDENT_COORDINATOR,
#         ):
#             student.department = request.user.department
            
#         student.save()
        
#         Registration.objects.get_or_create(
#             meet_event=meet_event,
#             participant=student,
#         )

#     return redirect("accounts:add_student_to_event", meet_event_id=meet_event.id)




@login_required
def coordinator_events(request):
    if not is_admin_or_coordinator(request.user):
        return HttpResponseForbidden("Not Allowed")
    
    # Show active meet events
    meet_events = MeetEvent.objects.filter(meet__status=MeetStatus.ACTIVE, is_active=True).select_related('event', 'meet')
    
    return render(request, "accounts/coordinator_events.html", {"meet_events": meet_events})



@login_required
def event_student_report(request):
    if not is_admin_or_coordinator_or_faculty(request.user):
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
            boys = [r for r in regs if r.participant.gender == "MALE"]
            girls = [r for r in regs if r.participant.gender == "FEMALE"]
            result.append({
                "meet_event": me,
                "event": me.event,
                "registrations": regs,
                "boys": boys,
                "girls": girls,
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
def download_event_report_pdf(request, meet_event_id, gender=None):
    if not is_admin_or_coordinator_or_faculty(request.user):
        return HttpResponseForbidden("Not allowed")

    meet_event = get_object_or_404(MeetEvent, id=meet_event_id)
    registrations = Registration.objects.filter(meet_event=meet_event).select_related('participant', 'participant__department')

    # Filter by gender if specified
    if gender == 'boys':
        data = [r for r in registrations if r.participant.gender == "MALE"]
        title_suffix = "Boys"
    elif gender == 'girls':
        data = [r for r in registrations if r.participant.gender == "FEMALE"]
        title_suffix = "Girls"
    else:
        # Combined report
        boys = [r for r in registrations if r.participant.gender == "MALE"]
        girls = [r for r in registrations if r.participant.gender == "FEMALE"]
        data = None
        title_suffix = "All"

    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, f"Event Report: {meet_event.event.name}", ln=True, align='C')
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 10, f"Meet: {meet_event.meet.name}", ln=True, align='C')
    if gender:
        pdf.cell(0, 10, f"Category: {title_suffix}", ln=True, align='C')
    pdf.ln(10)

    def add_table(title, table_data):
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, title, ln=True)
        pdf.ln(2)
        
        # Header
        pdf.set_font("helvetica", "B", 10)
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(50, 8, "Name", 1, 0, 'C', True)
        pdf.cell(30, 8, "Register No", 1, 0, 'C', True)
        pdf.cell(60, 8, "Department", 1, 0, 'C', True)
        pdf.cell(45, 8, "Email", 1, 1, 'C', True)
        
        # Data
        pdf.set_font("helvetica", "", 10)
        for r in table_data:
            pdf.cell(50, 8, str(r.participant.full_name)[:25], 1)
            pdf.cell(30, 8, str(r.participant.register_number), 1)
            pdf.cell(60, 8, str(r.participant.department.name if r.participant.department else "")[:30], 1)
            pdf.cell(45, 8, str(r.participant.email)[:25], 1)
            pdf.ln()
        pdf.ln(10)

    if data is not None:
        # Gender-specific report
        if data:
            add_table(title_suffix, data)
        else:
            pdf.set_font("helvetica", "I", 12)
            pdf.cell(0, 10, f"No {title_suffix.lower()} registered for this event.", ln=True)
    else:
        # Combined report
        if boys:
            add_table("Boys", boys)
        if girls:
            add_table("Girls", girls)
        if not boys and not girls:
            pdf.set_font("helvetica", "I", 12)
            pdf.cell(0, 10, "No students registered for this event.", ln=True)

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)

    filename = f"report_{meet_event.event.name}_{title_suffix}.pdf"
    return FileResponse(buf, as_attachment=True, filename=filename)


@login_required
def student_event_register(request, meet_event_id):
    if request.user.role != UserRole.STUDENT:
        return HttpResponseForbidden()

    meet_event = get_object_or_404(MeetEvent, id=meet_event_id)
    event = meet_event.event

    if event.status != EventStatus.ACTIVE:
        return HttpResponseForbidden()

    if request.user.gender == "MALE" and not event.gender_boys:
        return HttpResponseForbidden()

    if request.user.gender == "FEMALE" and not event.gender_girls:
        return HttpResponseForbidden()

    Registration.objects.get_or_create(
        meet_event=meet_event,
        participant=request.user
    )

    return redirect("accounts:student_dashboard")





@login_required
def student_manage(request):
    if request.user.role != UserRole.FACULTY_COORDINATOR:
        return HttpResponseForbidden()

    students = User.objects.filter(
        role=UserRole.STUDENT,
        registration__meet_event__event__event_type=EventType.INDIVIDUAL
    ).distinct()

    q = request.GET.get("q")
    if q:
        students = students.filter(
            Q(full_name__icontains=q) |
            Q(register_number__icontains=q)
        )

    return render(
        request,
        "accounts/student_manage.html",
        {
            "students": students
        }
    )


@login_required
def student_event_unregister(request, student_id):
    if request.user.role != UserRole.FACULTY_COORDINATOR:
        return HttpResponseForbidden()

    Registration.objects.filter(
        participant_id=student_id,
        meet_event__event__event_type=EventType.INDIVIDUAL
    ).delete()

    messages.success(
        request,
        "Student unregistered from individual events"
    )

    return redirect("accounts:student_manage")



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
def student_dashboard(request):
    if request.user.role != UserRole.STUDENT:
        return HttpResponseForbidden("Not allowed")
    
    # already registered events
    registrations = Registration.objects.filter(participant=request.user).select_related(
        "meet_event", "meet_event__event", "meet_event__meet"
    )
    
    registered_meet_event_ids = registrations.values_list("meet_event_id", flat=True)
    
    if request.user.gender == "MALE":
        q_gender = Q(event__gender_boys=True)
    else:
        q_gender = Q(event__gender_girls=True)


        
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
def create_team(request, meet_event_id):
    if request.user.role not in (
        UserRole.ADMIN,
        UserRole.FACULTY_COORDINATOR,
    ):
        return HttpResponseForbidden("Not allowed")

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

        team = Team.objects.create(
            meet_event=meet_event,
            name=name,
            created_by=request.user
        )

        messages.success(request, "Team created")
        return redirect(
            "accounts:manage_team_members",
            team_id=team.id
        )

    return render(
        request,
        "accounts/team/create_team.html",
        {"meet_event": meet_event}
    )





# @login_required
# def manage_team_members(request, team_id):
#     team = get_object_or_404(Team, id=team_id)
#     meet_event = team.meet_event
#     event = meet_event.event

#     if request.user.role not in (
#         UserRole.ADMIN,
#         UserRole.FACULTY_COORDINATOR,
#     ):
#         return HttpResponseForbidden("Not allowed")

#     students = User.objects.filter(
#         role=UserRole.STUDENT,
#         gender__in=[
#             "MALE" if event.gender_boys else "",
#             "FEMALE" if event.gender_girls else "",
#         ]
#     )

#     if request.user.role == UserRole.FACULTY_COORDINATOR:
#         students = students.filter(department=request.user.department)

#     members = TeamMember.objects.filter(team=team)

#     if request.method == "POST":
#         current_count = members.count()

#         if event.max_team_size and current_count >= event.max_team_size:
#             messages.error(request, "Team is already full")
#             return redirect(request.path)

#         student_id = request.POST.get("student")
#         student = get_object_or_404(User, id=student_id)

#         obj, created = TeamMember.objects.get_or_create(
#             team=team,
#             student=student
#         )

#         if not created:
#             messages.warning(request, "Student already in team")
#         else:
#             messages.success(request, "Student added")

#         return redirect(request.path)

#     return render(
#         request,
#         "accounts/team/manage_members.html",
#         {
#             "team": team,
#             "students": students,
#             "members": members,
#             "current_count": members.count(),
#             "max_size": event.max_team_size,
#             "is_full": event.max_team_size and members.count() >= event.max_team_size,
#         }
#     )






# @login_required
# def set_team_captain(request, team_id, member_id):
#     team = get_object_or_404(Team, id=team_id)

#     if request.user.role not in (
#         UserRole.ADMIN,
#         UserRole.FACULTY_COORDINATOR,
#     ):
#         return HttpResponseForbidden("Not allowed")

#     TeamMember.objects.filter(
#         team=team,
#         is_captain=True
#     ).update(is_captain=False)

#     member = get_object_or_404(
#         TeamMember,
#         id=member_id,
#         team=team
#     )
#     member.is_captain = True
#     member.save()

#     messages.success(request, "Captain assigned")
#     return redirect(
#         "accounts:manage_team_members",
#         team_id=team.id
#     )





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






@login_required
def results_dashboard(request):
    if not is_admin_or_coordinator(request.user):
        return HttpResponseForbidden("Not allowed")
    
    active_meets = Meet.objects.filter(status=MeetStatus.ACTIVE).prefetch_related('meetevent_set__event')
    return render(request, "accounts/results_dashboard.html", {"active_meets": active_meets})






@login_required
def manage_event_results(request, meet_event_id):
    if not is_admin_or_coordinator(request.user):
        return HttpResponseForbidden("Not allowed")
    
    meet_event = get_object_or_404(MeetEvent, id=meet_event_id)
    query = request.GET.get("q", "").strip()
    
    # Fetch all students instead of only registered ones
    students = User.objects.filter(role=UserRole.STUDENT).select_related('department')
    
    if query:
        students = students.filter(
            Q(full_name__icontains=query) |
            Q(register_number__icontains=query)
        )
    
    # Get registrations for this meet event to show positions
    regs = Registration.objects.filter(meet_event=meet_event)
    reg_map = {r.participant_id: r for r in regs}
    
    # Attach registration to student objects for template access
    for s in students:
        s.reg = reg_map.get(s.id)
    
    # Sort students: those with positions first, then alphabetically
    # In Python since we have the map now
    students = sorted(students, key=lambda x: (x.reg.position if x.reg and x.reg.position is not None else 999, x.full_name))
    
    return render(request, "accounts/manage_results.html", {
        "meet_event": meet_event,
        "students": students, # Changed from registrations to students
        "query": query
    })







@login_required
def set_registration_position(request, meet_event_id, student_id):
    if not is_admin_or_coordinator(request.user):
        return HttpResponseForbidden("Not allowed")
    
    meet_event = get_object_or_404(MeetEvent, id=meet_event_id)
    student = get_object_or_404(User, id=student_id, role=UserRole.STUDENT)
    
    # Get or create registration on the fly
    registration, created = Registration.objects.get_or_create(
        meet_event=meet_event,
        participant=student
    )
    
    position = request.POST.get("position")
    
    if position:
        try:
            pos_val = int(position)
            if pos_val < 0:
                registration.position = None
            else:
                registration.position = pos_val
            registration.save()
            messages.success(request, f"Updated position for {student.full_name}")
        except ValueError:
            messages.error(request, "Invalid position value")
            
    return redirect("accounts:manage_event_results", meet_event_id=meet_event.id)







@login_required
def export_results_pdf(request, meet_event_id):
    if not is_admin_or_coordinator(request.user):
        return HttpResponseForbidden("Not allowed")
    
    meet_event = get_object_or_404(MeetEvent, id=meet_event_id)
    winners = Registration.objects.filter(meet_event=meet_event, position__isnull=False).order_by('position')
    
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 10, f'Event Results: {meet_event.event.name}', 0, 1, 'C')
    pdf.set_font('helvetica', '', 12)
    pdf.cell(0, 10, f'Meet: {meet_event.meet.name}', 0, 1, 'C')
    pdf.ln(10)
    
    # Table Header
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(30, 10, 'Position', 1)
    pdf.cell(70, 10, 'Name', 1)
    pdf.cell(45, 10, 'Reg No', 1)
    pdf.cell(45, 10, 'Department', 1)
    pdf.ln()
    
    # Table Content
    pdf.set_font('helvetica', '', 11)
    for reg in winners:
        pdf.cell(30, 10, f"{reg.position}", 1)
        pdf.cell(70, 10, str(reg.participant.full_name)[:30], 1)
        pdf.cell(45, 10, str(reg.participant.register_number), 1)
        dept_name = reg.participant.department.name if reg.participant.department else "-"
        pdf.cell(45, 10, str(dept_name)[:20], 1)
        pdf.ln()
    
    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)
    
    return FileResponse(buf, as_attachment=True, filename=f"results_{meet_event.event.name.replace(' ', '_')}.pdf")