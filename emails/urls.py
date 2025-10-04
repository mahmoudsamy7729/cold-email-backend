from django.urls import path
from emails.views import EmailViewSet


app_name="emails"

email_create_list = EmailViewSet.as_view({
    "post": "create",
    "get": "list",
})
email_detail = EmailViewSet.as_view({"get": "retrieve"})
email_send_test = EmailViewSet.as_view({"post": "send_test"})



urlpatterns = [
    path("campaigns/<uuid:campaign_id>/emails/", email_create_list, name="email-list-create"),
    path("campaigns/<uuid:campaign_id>/emails/<uuid:id>/", email_detail, name="email-detail"),
    path("campaigns/<uuid:campaign_id>/emails/<uuid:id>/send-test/", email_send_test, name="email-send-test"),
]