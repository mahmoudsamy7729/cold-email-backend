import uuid
from django.db import models
from django.conf import settings
from django.db.models.functions import Lower
from django.db.models import Q, F

# Create your models here.

class ActiveManager(models.Manager):
    """Default manager: only non-archived rows."""
    def get_queryset(self):
        return super().get_queryset().exclude(status=CampaignStatus.ARCHIVED)

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CampaignStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SCHEDULED = "scheduled", "Scheduled"
    RUNNING = "running", "Running"
    PAUSED = "paused", "Paused"
    COMPLETED = "completed", "Completed"
    ARCHIVED = "archived", "Archived"


class ScheduleType(models.TextChoices):
    IMMEDIATE = "immediate", "Immediate"
    SCHEDULED = "scheduled", "Scheduled"

class Campaign(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="campaigns",
        db_index=True
    )
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=CampaignStatus.choices,
        default=CampaignStatus.DRAFT,
    )
    schedule_type = models.CharField(
        max_length=20,
        choices=ScheduleType.choices,
        default=ScheduleType.IMMEDIATE,
    )
    scheduled_at = models.DateTimeField(blank=True, null=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ("-created_at",)
        constraints = [
        # Enforce: for non-archived rows, (lower(name), user) must be unique
            models.UniqueConstraint(
                Lower("name"),
                "user",
                condition=~Q(status=CampaignStatus.ARCHIVED),
                name="uq_campaign_user_lower_name_active",
            ),
            # Enforce scheduled_at presence based on schedule_type
            models.CheckConstraint(
                name="ck_campaign_scheduled_at_matches_type",
                check=(
                    (Q(schedule_type=ScheduleType.SCHEDULED) & Q(scheduled_at__isnull=False)) |
                    (Q(schedule_type=ScheduleType.IMMEDIATE) & Q(scheduled_at__isnull=True))
                ),
            ),
        ]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["schedule_type"]),
            models.Index(fields=["scheduled_at"]),
            # Helpful for frequent queries
            models.Index(fields=["user", "status"], name="idx_campaign_user_status"),
            # Only for scheduled items (partial index)
            models.Index(
                fields=["user", "scheduled_at"],
                name="idx_camp_user_sched_active",
                condition=Q(status=CampaignStatus.SCHEDULED),
            ),
        ]

    def archive(self):
        self.status = CampaignStatus.ARCHIVED
        self.save(update_fields=["status", "updated_at"])

    def __str__(self):
        return self.name
