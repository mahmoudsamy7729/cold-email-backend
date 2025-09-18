from rest_framework import serializers
from .models import Audience
from audience.services.audience_validation import AudienceValidator


class AudienceSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Audience
        fields = (
            "id",
            "name",
            "description",
            "created_at",
            "updated_at",
            "user",            
        )

        read_only_fields = ("id", "created_at", "updated_at")

    def validate_name(self, value: str):
        user = self.context["request"].user
        return AudienceValidator.validate_name(user, value, instance=self.instance)