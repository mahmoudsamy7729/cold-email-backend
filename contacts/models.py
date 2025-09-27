import uuid
from django.db import models
from django.db.models.functions import Lower
from django.core.validators import RegexValidator
from django.db.models import Q
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex



from django.conf import settings




class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class ContactStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"
    UNSUBSCRIBED = "unsubscribed", "Unsubscribed"
    BOUNCED = "bounced", "Bounced"

class ContactSource(models.TextChoices):
    MANUAL = "manual", "Manual"
    API = "api", "API"
    FORM = "form", "Form Signup"
    CSV = "csv", "CSV Import"

class NonArchivedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(status=ContactStatus.ARCHIVED)

class Contact(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    audience = models.ForeignKey(
        "audience.Audience",
        on_delete=models.CASCADE,
        related_name="contacts",
    )
    email = models.EmailField()  # unique per audience (case-insensitive via UniqueConstraint below)
    first_name = models.CharField(max_length=120, blank=True)
    last_name = models.CharField(max_length=120, blank=True)

    phone_regex = RegexValidator(
        regex=r"^\+?[1-9]\d{7,14}$",
        message="Phone must be in international format (E.164), e.g., +201234567890.",
    )
    phone = models.CharField(max_length=16, blank=True, validators=[phone_regex])
    status = models.CharField(
        max_length=20,
        choices=ContactStatus.choices,
        default=ContactStatus.ACTIVE,
        db_index=True,
    )
    source = models.CharField(
        max_length=20,
        choices=ContactSource.choices,
        default=ContactSource.MANUAL,
        db_index=True,
    )

    tags = ArrayField(
        base_field=models.CharField(max_length=64),
        default=list,
        blank=True,
        help_text="List of lowercase tag names (user-scoped).",
    )

    objects = NonArchivedManager()
    all_objects = models.Manager()  # includes archived

    class Meta:
        constraints = [
             models.UniqueConstraint(
                Lower("email"), "audience",
                condition=~Q(status=ContactStatus.ARCHIVED),
                name="uniq_email_aud_active",
            ),
            # Email not empty only for NON-archived contacts
            models.CheckConstraint(
                condition=Q(status=ContactStatus.ARCHIVED) | ~Q(email=""),
                name="chk_email_not_empty_act",
            ),
        ]
        indexes = [
            GinIndex(fields=["tags"]),
            models.Index(
                Lower("email"),
                name="idx_email_active",
                condition=~Q(status=ContactStatus.ARCHIVED),
            ),
        ]
        ordering = ["-created_at"]

    def archive(self):

        if self.status != ContactStatus.ARCHIVED:
            self.status = ContactStatus.ARCHIVED
            self.save(update_fields=["status", "updated_at"])

    def __str__(self):
        base = f"{self.email} @ {getattr(self.audience, 'name')}"
        return f"{base} [{self.status}]"


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tags",
        db_index=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("name"), "user",
                name="uniq_tag_name_per_user_ci",  # case-insensitive unique
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.user})"



