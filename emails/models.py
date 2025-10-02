import uuid
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class EmailStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SCHEDULED = "scheduled", "Scheduled"
    QUEUING = "queuing", "Queuing"
    SENDING = "sending", "Sending"
    PAUSED = "paused", "Paused"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    FAILED = "failed", "Failed"

class Email(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Core relations
    campaign = models.ForeignKey(
        "campaigns.Campaign",
        on_delete=models.CASCADE,
        related_name="emails",
    )
    audience = models.ForeignKey(
        "audience.Audience",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emails",
        help_text="For first emails: whole audience. Can be null for future segments.",
    )
    depends_on = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="followups",
        help_text="If set, this email is a follow-up to another email.",
    )

    # Content & addressing
    subject = models.CharField(max_length=255)
    from_email = models.EmailField()
    from_name = models.CharField(max_length=255, null=True, blank=True)
    reply_to = models.EmailField(null=True, blank=True)

    content_text = models.TextField(
        blank=True,
        default="",
        help_text="Plain text body to send when no template is selected.",
    )

    
    # Template linkage (placeholder for future Templates app)
    template_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Nullable placeholder; later can be migrated to a proper FK.",
    )

     # Scheduling & status
    status = models.CharField(
        max_length=20,
        choices=EmailStatus.choices,
        default=EmailStatus.DRAFT,
        db_index=True,
    )
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When to start sending this email (UTC).",
    )


    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("campaign", "status")),
            models.Index(fields=("campaign", "scheduled_at")),
        ]

    def __str__(self) -> str:
        return f"{self.subject} [{self.status}]"

    # Optional guardrails you can keep or remove now:
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.scheduled_at and self.scheduled_at < timezone.now():
            raise ValidationError({"scheduled_at": "scheduled_at cannot be in the past."})
        if not self.content_text.strip():
            raise ValidationError({"content_text": "Content cannot be empty."})

    @property
    def uses_template(self) -> bool:
        return bool(self.template_id)