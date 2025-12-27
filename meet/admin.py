from django.contrib import admin

from accounts.admin import RoleAdminPermissionMixin
from accounts.admin_site import admin_site
from meet.models import Event, Meet, MeetEvent, Registration


class MeetEventInline(admin.TabularInline):
    model = MeetEvent
    extra = 1


@admin.register(Meet, site=admin_site)
class MeetAdmin(RoleAdminPermissionMixin, admin.ModelAdmin):
    model_key = "meet"

    list_display = ("name", "start_date", "end_date", "status")
    list_filter = ("status", "start_date", "end_date")
    search_fields = ("name",)
    inlines = (MeetEventInline,)


@admin.register(MeetEvent, site=admin_site)
class MeetEventAdmin(RoleAdminPermissionMixin, admin.ModelAdmin):
    model_key = "meet_event"
    list_display = ("meet", "event", "is_active")
    list_filter = ("meet", "event", "is_active")


@admin.register(Event, site=admin_site)
class EventAdmin(RoleAdminPermissionMixin, admin.ModelAdmin):
    model_key = "event"

    list_display = ("name",  "event_type", "status")
    list_filter = ("status", "event_type")
    search_fields = ("name", "event_type")
    

admin.site.register(Registration)