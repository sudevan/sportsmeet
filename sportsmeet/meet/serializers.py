from rest_framework import serializers
from .models import Meet, Event, Registration



class MeetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meet
        fields = "__all__"


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = "__all__"


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = "__all__"
        read_only_fields = ["participant", "registered_by"]
