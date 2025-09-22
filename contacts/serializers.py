from rest_framework import serializers
from .models import Contact
from .services.contact_validation import ContactService, DuplicateContactEmail


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            "id",
            "audience",
            "email",
            "first_name",
            "last_name",
            "phone",
            "status",
            "source",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "email": {"required": True},
            "audience": {"required": True},
        }

    def to_internal_value(self, data):
        for key in ["email", "first_name", "last_name", "phone"]:
            if key in data and isinstance(data[key], str):
                data[key] = data[key].strip()
        return super().to_internal_value(data)

    def validate_audience(self, audience):
        request = self.context["request"]
        if audience.user != request.user:
            raise serializers.ValidationError("No audience found for this id.")
        return audience

    def validate_email(self, value):
        audience = self.initial_data.get("audience") or getattr(self.instance, "audience", None)
        if audience:
            try:
                return ContactService.ensure_unique_email_in_audience(
                    email=value, audience_id=audience, instance=self.instance
                )
            except DuplicateContactEmail as e:
                raise serializers.ValidationError(str(e))
        return value