from django.contrib import admin
from .models import (
    Meet,
    Event,
    MeetEvent,
    Team,
    TeamMember,
    Registration,
)


@admin.register(Meet)
class MeetAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "status")
    list_filter = ("status",)
    search_fields = ("name",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "event_type", "category", "status", "max_team_size")
    list_filter = ("event_type", "category", "status")
    search_fields = ("name",)


@admin.register(MeetEvent)
class MeetEventAdmin(admin.ModelAdmin):
    list_display = ("meet", "event", "is_active")
    list_filter = ("is_active",)
    search_fields = ("meet__name", "event__name")


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("meet_event", "department")
    list_filter = ("department",)
    search_fields = ("department__name",)


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("student", "team")
    search_fields = ("student__full_name", "student__register_number")


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("participant", "meet_event", "position")
    list_filter = ("meet_event",)
    search_fields = ("participant__full_name", "participant__register_number")
