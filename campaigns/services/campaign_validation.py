from rest_framework.exceptions import ValidationError
from campaigns.models import Campaign, CampaignStatus


class CampaignValidator:
    @staticmethod
    def validate_name(user, name:str, instance=None):
        valid_name = (name or "").strip().lower()
        if not valid_name:
            raise ValidationError("Name cannot be blank.")

        qs = Campaign.objects.filter(user=user, name__iexact=name.strip())
        if instance:
            qs = qs.exclude(pk=instance.pk)

        if qs.exists():
            raise ValidationError("You already have an active campaign with this name.")

        return name