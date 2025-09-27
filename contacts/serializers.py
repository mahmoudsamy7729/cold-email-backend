from rest_framework import serializers
from django.db import transaction
from .services.contact_validation import ContactService, DuplicateContactEmail
from .models import Contact
from audience.models import Audience


class ContactSerializer(serializers.ModelSerializer):
    audience = serializers.PrimaryKeyRelatedField(
        queryset=Audience.objects.all()
    )
    tags = serializers.ListField(
        child=serializers.CharField(max_length=64),
        required=False
    )

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
            "tags",
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
    
    
    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        tags = validated_data.pop("tags", [])
        tags = ContactService.normalize_tags(tags)
        contact = Contact.objects.create(**validated_data, tags=tags)
        if tags:
            ContactService.get_or_create_tags(user, tags)

        return contact
    
    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context["request"].user
        tags = validated_data.pop("tags", None)

        if tags is not None:
            tags = ContactService.normalize_tags(tags)
            instance.tags = tags
            if tags:
                ContactService.get_or_create_tags(user, tags)

        return super().update(instance, validated_data)
