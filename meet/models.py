from django.db import models
from django.core.exceptions import ValidationError
from accounts.models import Department, Student


class MeetStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    ACTIVE = "ACTIVE", "Active"
    COMPLETED = "COMPLETED", "Completed"


class EventStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"


class EventCategory(models.TextChoices):
    TRACK = "TRACK", "Track"
    FIELD = "FIELD", "Field"
    OTHER = "OTHER", "Other"


class EventType(models.TextChoices):
    INDIVIDUAL = "INDIVIDUAL", "Individual"
    TEAM = "TEAM", "Team"


class Meet(models.Model):
    name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=16,
        choices=MeetStatus.choices,
        default=MeetStatus.DRAFT
    )

    def __str__(self):
        return self.name


class Event(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(
        max_length=20,
        choices=EventCategory.choices,
        default=EventCategory.OTHER
    )
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        default=EventType.INDIVIDUAL
    )
    max_team_size = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=EventStatus.choices,
        default=EventStatus.ACTIVE
    )

    def clean(self):
        if self.event_type == EventType.INDIVIDUAL:
            self.max_team_size = None
        if self.event_type == EventType.TEAM and not self.max_team_size:
            raise ValidationError("Maximum team size is required")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class MeetEvent(models.Model):
    meet = models.ForeignKey(Meet, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("meet", "event")

    def __str__(self):
        return f"{self.meet} - {self.event}"


class Team(models.Model):
    meet_event = models.ForeignKey(
        MeetEvent, on_delete=models.CASCADE, related_name="teams"
    )
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("meet_event", "department")

    def __str__(self):
        return f"{self.meet_event.event.name} - {self.department.name}"


class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("team", "student")

    def clean(self):
        event = self.team.meet_event.event

        if self.student.department != self.team.department:
            raise ValidationError("Student must belong to same department")

        if event.max_team_size:
            if TeamMember.objects.filter(team=self.team).exclude(id=self.id).count() >= event.max_team_size:
                raise ValidationError("Team is full")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Registration(models.Model):
    meet_event = models.ForeignKey(
        MeetEvent, on_delete=models.CASCADE, related_name="registrations"
    )
    participant = models.ForeignKey(Student, on_delete=models.CASCADE)
    position = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("meet_event", "participant")

    def clean(self):
        if self.meet_event.event.event_type == EventType.TEAM:
            raise ValidationError("Direct registration not allowed for team events")

        if self.meet_event.meet.status != MeetStatus.ACTIVE:
            raise ValidationError("Meet is not active")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
