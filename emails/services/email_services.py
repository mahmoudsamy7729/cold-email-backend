# emails/services/email_service.py
from typing import Dict, Any
from django.core.exceptions import ValidationError
from django.db import transaction
from emails.models import Email
from audience.models import Audience

class PermissionDeniedError(Exception):
    pass

@transaction.atomic
def create_email_draft(*, user, campaign_id, data: Dict[str, Any]) -> Email:
    """
    Minimal business logic for creating an Email draft.
    - Injects campaign_id
    - Ensures audience belongs to the user
    - Ensures depends_on (if provided) belongs to same user & campaign
    - Validates required fields at the domain level
    """
    audience = data.get("audience")
    if not isinstance(audience, Audience):
        raise ValidationError({"audience": "Invalid audience."})
    if audience.user_id != user.id:
        raise PermissionDeniedError("You don't own this audience.")

    depends_on = data.get("depends_on")
    if depends_on is not None:
        # must be same user and same campaign
        if depends_on.campaign.user_id != user.id:
            raise PermissionDeniedError("You don't own the depends_on email.")
        if str(depends_on.campaign_id) != str(campaign_id):
            raise ValidationError({"depends_on": "Must belong to the same campaign."})

    # required-on-create bundle
    missing = []
    for key in ("subject", "content_text", "from_email"):
        v = (data.get(key) or "").strip() if isinstance(data.get(key), str) else data.get(key)
        if not v:
            missing.append(key)
    if missing:
        raise ValidationError({f: "This field is required." for f in missing})

    # Create the draft
    email = Email.objects.create(campaign_id=campaign_id, **data)
    return email
