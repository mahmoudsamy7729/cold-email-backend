from rest_framework.routers import DefaultRouter
from .views import AudienceViewSet

app_name = "audience"


router = DefaultRouter()
router.register(r"audiences", AudienceViewSet, basename="audience")
urlpatterns = router.urls