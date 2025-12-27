from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import Meet, Event, Registration
from .serializers import MeetSerializer, EventSerializer, RegistrationSerializer
from .permissions import IsAdminOrCoordinator



class MeetViewSet(ModelViewSet):
    queryset = Meet.objects.all()
    serializer_class = MeetSerializer
    permission_classes = [IsAuthenticated, IsAdminOrCoordinator]



class EventViewSet(ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, IsAdminOrCoordinator]



class RegistrationViewSet(ModelViewSet):
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Students see only their registrations
        return Registration.objects.filter(participant=self.request.user)

    def perform_create(self, serializer):
        event = serializer.validated_data["event"]

        if event.meet.status != "ACTIVE":
            raise PermissionDenied("Meet is not active")

        serializer.save(
            participant=self.request.user,
            registered_by=self.request.user
        )

