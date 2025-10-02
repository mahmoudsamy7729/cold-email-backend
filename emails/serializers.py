from rest_framework import serializers
from django.utils import timezone
from emails.models import Email, EmailStatus
from campaigns.models import Campaign
from audience.models import Audience

class EmailSerializer(serializers.ModelSerializer):
    # Client must NOT send campaign in body; it comes from URL.
    campaign = serializers.UUIDField(write_only=True, required=False)  # ignored on create
    audience = serializers.PrimaryKeyRelatedField(
        queryset=Audience.objects.all(), required=True
    )

    class Meta:
        model = Email
        fields = [
            "id",
            "campaign",          # write_only (ignored on create; useful for updates if you allow moving emails)
            "audience",
            "depends_on",
            "subject",
            "from_email",
            "from_name",
            "reply_to",
            "content_text",
            "template_id",
            "status",
            "scheduled_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

    # --- Required fields on creation ---
    def validate(self, attrs):
        request = self.context["request"]
        is_create = request.method == "POST"

        # Required on create
        if is_create:
            missing = []
            for key in ("audience", "subject", "content_text", "from_email"):
                if not attrs.get(key) or (key == "content_text" and not attrs.get(key).strip()):
                    missing.append(key)
            if missing:
                raise serializers.ValidationError(
                    {"detail": f"Missing required fields: {', '.join(missing)}"}
                )

        # scheduled_at guard
        scheduled_at = attrs.get("scheduled_at")
        if scheduled_at and scheduled_at < timezone.now():
            raise serializers.ValidationError({"scheduled_at": "cannot be in the past"})

        return attrs

    def validate_audience(self, audience: Audience):
        # Ensure audience belongs to the authenticated user
        request = self.context["request"]
        if audience.user_id != request.user.id:
            raise serializers.ValidationError("Invalid audience.")
        return audience

    def validate_depends_on(self, parent: Email):
        # If set, it must belong to the same user (and later, same campaign)
        if parent is None:
            return parent
        request = self.context["request"]
        if parent.campaign.user_id != request.user.id:
            raise serializers.ValidationError("Invalid depends_on reference.")
        return parent

    # --- Create: inject campaign from URL ---
    def create(self, validated_data):
        """
        Expect a nested route like:
          POST /api/campaigns/{campaign_id}/emails/
        The view should pass campaign_id in self.context["campaign_id"] from the URL kwarg.
        """
        campaign_id = self.context.get("campaign_id")
        if not campaign_id:
            # Fallback if the view didn’t pass it explicitly (e.g., using kwargs)
            campaign_id = self.context.get("view").kwargs.get("campaign_id") or \
                          self.context.get("view").kwargs.get("campaign_pk")  # depending on your router name

        if not campaign_id:
            raise serializers.ValidationError({"campaign": "campaign_id missing from URL."})

        try:
            campaign = Campaign.objects.get(id=campaign_id, user=self.context["request"].user)
        except Campaign.DoesNotExist:
            raise serializers.ValidationError({"campaign": "Not found."})

        # Don’t allow the client to override campaign in the body
        validated_data.pop("campaign", None)

        email = Email.objects.create(campaign=campaign, **validated_data)
        return email
