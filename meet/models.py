from django.db import models
from django.core.exceptions import ValidationError
from accounts.models import User


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

    @property
    def events(self):
        return Event.objects.filter(
            meetevent__meet=self,
            meetevent__is_active=True
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

        if self.event_type == EventType.TEAM:
            if not self.max_team_size:
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
        MeetEvent,
        on_delete=models.CASCADE,
        related_name="teams"
    )
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("meet_event", "name")

    def clean(self):
        event = self.meet_event.event

        if event.event_type != EventType.TEAM:
            raise ValidationError("Teams allowed only for TEAM events")

        member_count = TeamMember.objects.filter(team=self).count()

        if event.max_team_size and member_count >= event.max_team_size:
            raise ValidationError(
                f"Maximum {event.max_team_size} players allowed"
            )



    def __str__(self):
        return self.name


class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    is_captain = models.BooleanField(default=False)

    class Meta:
        unique_together = ("team", "student")

    def clean(self):
        if self.is_captain:
            if TeamMember.objects.filter(
                team=self.team,
                is_captain=True
            ).exclude(id=self.id).exists():
                raise ValidationError("Only one captain allowed")
            
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)



class Registration(models.Model):
    meet_event = models.ForeignKey(
        MeetEvent,
        on_delete=models.CASCADE,
        related_name="registrations"
    )
    participant = models.ForeignKey(User, on_delete=models.CASCADE)
    position = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("meet_event", "participant")

    def clean(self):
        event = self.meet_event.event
        student = self.participant

        if self.meet_event.meet.status != MeetStatus.ACTIVE:
            raise ValidationError("Meet is not active")

        if event.status != EventStatus.ACTIVE:
            raise ValidationError("Event is not active")

        # Gender-based separation happens here (same as before)
        if student.gender not in ("MALE", "FEMALE"):
            raise ValidationError("Invalid student gender")


    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
