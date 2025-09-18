from rest_framework.exceptions import ValidationError
from audience.models import Audience


class AudienceValidator:
    @staticmethod
    def validate_name(user, name: str, instance=None) -> str:
        name = (name or "").strip()
        if not name:
            raise ValidationError("Name cannot be blank.")

        qs = Audience.all_objects.filter(user=user, name=name, archived_at__isnull=True)
        if instance:
            qs = qs.exclude(pk=instance.pk)

        if qs.exists():
            raise ValidationError("You already have an active audience with this name.")

        return name