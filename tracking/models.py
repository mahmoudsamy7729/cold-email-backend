import uuid
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class RecipientStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    SENT = "sent", "Sent"
    DELIVERED = "delivered", "Delivered"
    BOUNCED = "bounced", "Bounced"
    COMPLAINED = "complained", "Complained"
    UNSUBSCRIBED = "unsubscribed", "Unsubscribed"
    OPENED = "opened", "Opened"
    CLICKED = "clicked", "Clicked"


class EmailRecipient(TimeStampedModel):
    """
    One record per (Email, Contact).
    Tracks the latest status of that contact for the given email.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.ForeignKey(
        "emails.Email",
        on_delete=models.CASCADE,
        related_name="recipients",
    )
    contact = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.CASCADE,
        related_name="email_recipients",
    )

    status = models.CharField(
        max_length=20,
        choices=RecipientStatus.choices,
        default=RecipientStatus.QUEUED,
        db_index=True,
    )
    provider_message_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="ID returned by ESP/SMTP provider for this recipient."
    )
    last_event_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("email", "contact")
        indexes = [
            models.Index(fields=("email", "status")),
            models.Index(fields=("contact", "status")),
        ]

    def __str__(self):
        return f"{self.contact_id} → {self.email_id} [{self.status}]"


class TrackEvent(TimeStampedModel):
    """
    Append-only event log for recipient interactions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    recipient = models.ForeignKey(
        EmailRecipient,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(
        max_length=20,
        choices=RecipientStatus.choices,
        db_index=True,
    )
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=("recipient", "event_type")),
            models.Index(fields=("event_type", "occurred_at")),
        ]

    def __str__(self):
        return f"{self.recipient_id} → {self.event_type} @ {self.occurred_at}"