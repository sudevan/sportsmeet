from django.urls import path
from . import views

app_name = "accounts"


urlpatterns = [
    path("", views.home, name="home"),
    path("students/", views.student_list, name="student_list"),
    path("students/upload/", views.student_bulk_upload, name="student_bulk_upload"),
    path("students/search/", views.student_search, name="student_search"),
]
urlpatterns += [
    path(
        "events/<int:meet_event_id>/add-students/",
        views.add_student_to_event,
        name="add_student_to_event",
    ),
    path(
        "events/<int:meet_event_id>/add-existing/<int:student_id>/",
        views.register_existing_student,
        name="register_existing_student",
    ),
    path("coordinator/events/", views.coordinator_events, name="coordinator_events"),
    path(
        "reports/event-students/",
        views.event_student_report,
        name="event_student_report",
    ),
    path(
        "reports/event-students/<int:meet_event_id>/pdf/boys/",
        views.download_event_report_pdf,
        {'gender': 'boys'},
        name="download_boys_report_pdf",
    ),
    path(
        "reports/event-students/<int:meet_event_id>/pdf/girls/",
        views.download_event_report_pdf,
        {'gender': 'girls'},
        name="download_girls_report_pdf",
    ),
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
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("student/dashboard/",
         views.student_dashboard,
         name= "student_dashboard"
    ),
    path("student/register/<int:meet_event_id>/",
        views.student_event_register,
        name="student_event_register"   
    ),
    path(
        "admin/meet/<int:meet_id>/assign-events/",
        views.admin_meet_event_assign,
        name="admin_meet_event_assign"
    ),
    path(
        "faculty_coordinator/assign-meets-to-events/<int:meet_id>",
        views.faculty_assign_events_to_meet,
        name = "faculty_assign_events_to_meet"
    ),
    path(
        "admin-dashboard/",
        views.admin_dashboard,
        name="admin_dashboard"
    ),
    path("admin/create-meet/", views.admin_create_meet, name="admin_create_meet"),
    path("admin/create-event/", views.admin_create_event, name="admin_create_event"),
    path(
        "team/create/<int:meet_event_id>/",
        views.create_team,
        name="create_team"
    ),
    path(
        "team/<int:team_id>/members/",
        views.manage_team_members,
        name="manage_team_members"
    ),
    path(
        "team/<int:team_id>/set-captain/<int:member_id>/",
        views.set_team_captain,
        name="set_team_captain"
    ),
    path(
        "events/<int:meet_event_id>/export-pdf-registrations/",
        views.export_registered_students_pdf,
        name="export_registered_students_pdf"
    ),
    path("results/", views.results_dashboard, name="results_dashboard"),
    path("results/event/<int:meet_event_id>/", views.manage_event_results, name="manage_event_results"),
    path("results/set-position/<int:meet_event_id>/<int:student_id>/", views.set_registration_position, name="set_registration_position"),
    path("results/export-pdf/<int:meet_event_id>/", views.export_results_pdf, name="export_results_pdf"),
    path(
        "students/manage/",
        views.student_manage,
        name="student_manage"
    ),

    path(
        "team/events/manage/",
        views.team_events_manage,
        name="team_events_manage"
    ),

]
