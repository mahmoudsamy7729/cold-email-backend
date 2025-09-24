from rest_framework import serializers
from .models import Audience
from audience.services.audience_validation import AudienceValidator


class AudienceSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    contacts_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Audience
        fields = (
            "id",
            "name",
            "description",
            "created_at",
            "updated_at",
            "user",    
            "contacts_count",        
        )

        read_only_fields = ("id", "created_at", "updated_at", "contacts_count")

    def validate_name(self, value: str):
        user = self.context["request"].user
        return AudienceValidator.validate_name(user, value, instance=self.instance)