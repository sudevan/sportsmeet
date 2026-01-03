from django.urls import path
<<<<<<< HEAD
from .views import home, student_bulk_upload, student_search, student_list,add_student_to_event, register_existing_student,  add_new_student_and_register, coordinator_events, event_student_report, faculty_coordinator_dashboard, student_coordinator_dashboard, login_view, logout_view, student_dashboard, student_event_register, faculty_dashboard, admin_meet_event_assign, faculty_assign_events_to_meet, admin_dashboard, admin_create_meet, admin_create_event, create_team, manage_team_members, set_team_captain, team_registration_report, download_individual_event_pdf, download_team_pdf, edit_team, remove_team_member, team_events_manage, student_manage, student_event_unregister
=======
from .views import home, student_bulk_upload, student_search, student_list,add_student_to_event, register_existing_student,  add_new_student_and_register, coordinator_events, event_student_report, download_event_report_pdf, faculty_coordinator_dashboard, student_coordinator_dashboard, login_view, logout_view, student_dashboard, student_event_register, faculty_dashboard, admin_meet_event_assign, faculty_assign_events_to_meet, admin_dashboard, admin_create_meet, admin_create_event, create_team, manage_team_members, set_team_captain, export_registered_students_pdf, results_dashboard, manage_event_results, set_registration_position, export_results_pdf
>>>>>>> 08fcc5a013bce4b3cebebca9d464789909adb068

app_name = "accounts"

urlpatterns = [
    path("", home, name="home"),
    path("students/", student_list, name="student_list"),
    path("students/upload/", student_bulk_upload, name="student_bulk_upload"),
    path("students/search/", student_search, name="student_search"),
]
urlpatterns += [
    path(
        "events/<int:meet_event_id>/add-students/",
        add_student_to_event,
        name="add_student_to_event",
    ),
    path(
        "events/<int:meet_event_id>/add-existing/<int:student_id>/",
        register_existing_student,
        name="register_existing_student",
    ),
    path(
        "events/<int:meet_event_id>/add-new/",
        add_new_student_and_register,
        name="add_new_student_and_register",
    ),
    path("coordinator/events/", coordinator_events, name="coordinator_events"),
    path(
        "reports/event-students/",
        event_student_report,
        name="event_student_report",
    ),
    path(
        "reports/event-students/<int:meet_event_id>/pdf/boys/",
        download_event_report_pdf,
        {'gender': 'boys'},
        name="download_boys_report_pdf",
    ),
    path(
        "reports/event-students/<int:meet_event_id>/pdf/girls/",
        download_event_report_pdf,
        {'gender': 'girls'},
        name="download_girls_report_pdf",
    ),
    path(
        "faculty/coordinator/dashboard/",
        faculty_coordinator_dashboard,
        name="faculty_coordinator_dashboard",
    ),
    path(
        "faculty/dashboard/",
        faculty_dashboard,
        name="faculty_dashboard",
    ),
    path(
        "student-coordinator/dashboard/",
        student_coordinator_dashboard,
        name="student_coordinator_dashboard",
    ),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("student/dashboard/",
         student_dashboard,
         name= "student_dashboard"
    ),
    path("student/register/<int:meet_event_id>/",
        student_event_register,
        name="student_event_register"   
    ),
    path(
        "admin/meet/<int:meet_id>/assign-events/",
        admin_meet_event_assign,
        name="admin_meet_event_assign"
    ),
    path(
        "faculty_coordinator/assign-meets-to-events/<int:meet_id>",
        faculty_assign_events_to_meet,
        name = "faculty_assign_events_to_meet"
    ),
    path(
        "admin-dashboard/",
        admin_dashboard,
        name="admin_dashboard"
    ),
    path("admin/create-meet/", admin_create_meet, name="admin_create_meet"),
    path("admin/create-event/", admin_create_event, name="admin_create_event"),
    path(
        "team/create/<int:meet_event_id>/",
        create_team,
        name="create_team"
    ),
    path(
        "team/<int:team_id>/members/",
        manage_team_members,
        name="manage_team_members"
    ),
    path(
        "team/<int:team_id>/set-captain/<int:member_id>/",
        set_team_captain,
        name="set_team_captain"
    ),
<<<<<<< HEAD
    path("reports/teams/", team_registration_report, name="team_registration_report"),

    path(
        "reports/individual/<int:meet_event_id>/pdf/",
        download_individual_event_pdf,
        name="download_individual_event_pdf"
    ),

    path(
        "reports/team/<int:team_id>/pdf/",
        download_team_pdf,
        name="download_team_pdf"
    ),
    path(
        "team/<int:team_id>/edit/",
        edit_team,
        name="edit_team"
    ),
    path(
        "team/<int:team_id>/remove-member/<int:member_id>/",
        remove_team_member,
        name="remove_team_member"
    ),
    path(
        "team-events/",
        team_events_manage,
        name="team_events_manage"
    ),
    path(
        "students/manage/",
        student_manage,
        name="student_manage"
    ),
    path(
        "student-event-edit/<int:student_id>/",
        student_event_unregister,
        name="student_event_unregister"
    )
=======
    path(
        "events/<int:meet_event_id>/export-pdf-registrations/",
        export_registered_students_pdf,
        name="export_registered_students_pdf"
    ),
    path("results/", results_dashboard, name="results_dashboard"),
    path("results/event/<int:meet_event_id>/", manage_event_results, name="manage_event_results"),
    path("results/set-position/<int:meet_event_id>/<int:student_id>/", set_registration_position, name="set_registration_position"),
    path("results/export-pdf/<int:meet_event_id>/", export_results_pdf, name="export_results_pdf"),
>>>>>>> 08fcc5a013bce4b3cebebca9d464789909adb068
]
