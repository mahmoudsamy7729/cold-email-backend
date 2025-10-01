from django.utils import timezone
from rest_framework import serializers
from .models import Campaign, CampaignStatus, ScheduleType
from campaigns.services.campaign_validation import CampaignValidator


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = (
            "id",
            "name",
            "description",
            "status",
            "schedule_type",
            "scheduled_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


    def validate_name(self, value: str):
        user = self.context["request"].user

        return CampaignValidator.validate_name(user, value, instance=self.instance)

    def validate(self, attrs):
        print("User input data: ", attrs)
        schedule_type = attrs.get("schedule_type", getattr(self.instance, "schedule_type", None))
        scheduled_at = attrs.get("scheduled_at", getattr(self.instance, "scheduled_at", None))

        if schedule_type == ScheduleType.IMMEDIATE and scheduled_at is not None:
            raise serializers.ValidationError({"scheduled_at": "Must be empty for immediate campaigns."})

        if schedule_type == ScheduleType.SCHEDULED:
            if scheduled_at is None:
                raise serializers.ValidationError({"scheduled_at": "Required when schedule_type is 'scheduled'."})
            if timezone.is_naive(scheduled_at):
                raise serializers.ValidationError({"scheduled_at": "Datetime must be timezone-aware."})

        return attrs