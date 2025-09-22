from rest_framework.routers import DefaultRouter
from .views import ContactViewSet

app_name = "contacts"


router = DefaultRouter()
router.register(r"contacts", ContactViewSet, basename="contact")
urlpatterns = router.urls