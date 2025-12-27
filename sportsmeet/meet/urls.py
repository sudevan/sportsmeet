from rest_framework.routers import DefaultRouter
from .views import MeetViewSet, EventViewSet, RegistrationViewSet

router = DefaultRouter()
router.register("meets", MeetViewSet)
router.register("events", EventViewSet)
router.register("registrations", RegistrationViewSet, basename="registration")


urlpatterns = router.urls
