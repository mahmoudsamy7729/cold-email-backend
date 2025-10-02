from rest_framework import viewsets, permissions
from rest_framework.exceptions import NotFound
from emails.models import Email
from emails.serializers import EmailSerializer

class EmailViewSet(viewsets.ModelViewSet):
    serializer_class = EmailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def _campaign_id(self):
        cid = self.kwargs.get("campaign_id")
        if not cid:
            # Guard hard: if this route is hit without campaign_id something is miswired
            raise NotFound(detail="campaign_id not provided in URL.")
        return cid

    def get_queryset(self):
        campaign_id = self._campaign_id()
        # Filter by BOTH user and campaign
        return (
            Email.objects
            .filter(campaign__user=self.request.user, campaign_id=campaign_id)
            .select_related("campaign", "audience")
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["campaign_id"] = self._campaign_id()
        return ctx