from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [

    # ==================================================
    # PUBLIC (NO LOGIN REQUIRED)
    # ==================================================
    path("", views.public_home, name="public_home"),
    path("home/", views.home, name="home"),
    path("register/", views.student_register, name="student_register"),

    # ==================================================
    # AUTH (ONLY ADMIN / FACULTY / COORDINATORS)
    # ==================================================
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # ==================================================
    # DASHBOARDS (LOGIN REQUIRED)
    # ==================================================
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),

    path(
        "faculty/coordinator/dashboard/",
        views.faculty_coordinator_dashboard,
        name="faculty_coordinator_dashboard",
    ),

    path(
        "faculty/dashboard/",
        views.faculty_dashboard,
        name="faculty_dashboard",
    ),

    path(
        "student-coordinator/dashboard/",
        views.student_coordinator_dashboard,
        name="student_coordinator_dashboard",
    ),

    # ==================================================
    # MEET & EVENT MANAGEMENT
    # ==================================================
    path("admin/create-meet/", views.admin_create_meet, name="admin_create_meet"),
    path("admin/create-event/", views.admin_create_event, name="admin_create_event"),

    path(
        "admin/meet/<int:meet_id>/assign-events/",
        views.admin_meet_event_assign,
        name="admin_meet_event_assign",
    ),

    path(
        "faculty/meet/<int:meet_id>/assign-events/",
        views.faculty_assign_events_to_meet,
        name="faculty_assign_events_to_meet",
    ),

    # ==================================================
    # EVENT LISTING & STUDENTS
    # ==================================================
    path(
        "events/",
        views.student_list,
        name="student_list",
    ),

    path(
        "events/<int:meet_event_id>/students/",
        views.event_students,
        name="event_students",
    ),

    # ==================================================
    # STUDENT SEARCH (STAFF ONLY)
    # ==================================================
    path("students/search/", views.student_search, name="student_search"),

    # ==================================================
    # REPORTS
    # ==================================================
    path(
        "reports/event-students/",
        views.event_student_report,
        name="event_student_report",
    ),

    path(
        "reports/event-students/<int:meet_event_id>/pdf/boys/",
        views.download_event_report_pdf,
        {"gender": "boys"},
        name="download_boys_report_pdf",
    ),

    path(
        "reports/event-students/<int:meet_event_id>/pdf/girls/",
        views.download_event_report_pdf,
        {"gender": "girls"},
        name="download_girls_report_pdf",
    ),

    # ==================================================
    # RESULTS
    # ==================================================
    path("results/", views.results_dashboard, name="results_dashboard"),

    path(
        "results/event/<int:meet_event_id>/",
        views.manage_event_results,
        name="manage_event_results",
    ),

    path(
        "results/set-position/<int:meet_event_id>/<int:student_id>/",
        views.set_registration_position,
        name="set_registration_position",
    ),

    path(
        "results/export-pdf/<int:meet_event_id>/",
        views.export_results_pdf,
        name="export_results_pdf",
    ),
]
