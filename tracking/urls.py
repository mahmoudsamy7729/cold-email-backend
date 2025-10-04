from django.urls import path
from tracking.views import ClickRedirectView, UnsubscribeView

urlpatterns = [
    path("t/c", ClickRedirectView.as_view(), name="track-click"),
    path("t/u", UnsubscribeView.as_view(), name="track-unsubscribe"),
]