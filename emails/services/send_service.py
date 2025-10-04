from typing import Dict
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django.utils.html import escape
from django.core.mail import EmailMultiAlternatives

from emails.models import Email
from audience.models import Audience
from tracking.models import EmailRecipient, RecipientStatus
from tracking.rewrite import rewrite_html_links

from .email_services import PermissionDeniedError


def _assert_ownership(user_id: int, email: Email) -> None:
    # campaign.user validated to current user
    if email.campaign.user_id != user_id:
        raise PermissionDeniedError("You don't own this email.")

    if not isinstance(email.audience, Audience):
        raise ValidationError({"audience": "Email has no audience."})
    if email.audience.user_id != user_id:
        raise PermissionDeniedError("You don't own the audience linked to this email.")


def _pick_test_contact(email: Email):
    # Simple: first contact in the audience with a non-empty email
    contact = email.audience.contacts.filter().order_by("id").first()
    if not contact:
        raise ValidationError({"audience": "Audience has no contacts."})
    if not contact.email:
        raise ValidationError({"contact": "Selected contact has no email."})
    return contact


def _build_html_from_plain(plain: str) -> str:
    # minimal safe HTML wrapping + newline → <br>
    plain = plain or ""
    formatted = escape(plain).replace("\n", "<br>")
    return f"<div>{formatted}</div>"



def send_test_email(*, request, user, email: Email) -> Dict:
    """
    Sends a single test message to the first contact in the email's audience.
    - Validates ownership & audience
    - Creates/updates an EmailRecipient row
    - Rewrites links for tracking
    - Sends via Django email backend
    Returns: {"status": "sent", "to": "<address>"} (or raises)
    """
    _assert_ownership(user.id, email)
    contact = _pick_test_contact(email)

    recipient, _ = EmailRecipient.objects.get_or_create(
        email=email,
        contact=contact,
        defaults={"status": RecipientStatus.QUEUED},
    )

    plain = email.content_text or ""
    html = _build_html_from_plain(plain)
    html_tracked = rewrite_html_links(request, html, str(recipient.id))

    from_addr = email.from_email or settings.DEFAULT_FROM_EMAIL
    subject = email.subject or "(no subject)"
    to_list = [contact.email]

    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain,
        from_email=from_addr if not email.from_name else f"{email.from_name} <{from_addr}>",
        to=to_list,
        reply_to=[email.reply_to] if email.reply_to else None,
    )
    msg.attach_alternative(html_tracked, "text/html")

    # Try to send
    msg.send(fail_silently=False)

    # Update recipient status on success
    recipient.status = RecipientStatus.SENT
    recipient.save(update_fields=["status", "updated_at"])

    return {"status": "sent", "to": contact.email}
