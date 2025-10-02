from django.urls import path
from emails.views import EmailViewSet

email_create_list = EmailViewSet.as_view({
    "post": "create",
    "get": "list",
})
email_detail = EmailViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    path("campaigns/<uuid:campaign_id>/emails/", email_create_list, name="email-list-create"),
    path("campaigns/<uuid:campaign_id>/emails/<uuid:id>/", email_detail, name="email-detail"),
]