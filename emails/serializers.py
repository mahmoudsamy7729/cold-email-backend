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

    def validate(self, attrs):
        scheduled_at = attrs.get("scheduled_at")
        if scheduled_at and scheduled_at < timezone.now():
            raise serializers.ValidationError({"scheduled_at": "cannot be in the past"})
        return attrs

    def validate_audience(self, audience: Audience):
        if audience.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("Invalid audience.")
        return audience

    def validate_depends_on(self, parent: Email):
        if parent is None:
            return parent
        request = self.context["request"]
        if parent.campaign.user_id != request.user.id:
            raise serializers.ValidationError("Invalid depends_on reference.")
        return parent
