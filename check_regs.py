import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from meet.models import MeetEvent, Registration

me = MeetEvent.objects.filter(meet__name__icontains='foodball', event__name__icontains='hig jump').first()
if me:
    print(f"MeetEvent ID: {me.id}")
    regs = Registration.objects.filter(meet_event=me)
    print(f"Registration count: {regs.count()}")
    for r in regs:
        print(f" - {r.participant.full_name} ({r.participant.register_number})")
else:
    print("MeetEvent not found")
