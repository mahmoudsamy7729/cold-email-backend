import uuid
import time
import hashlib
from django.utils.text import slugify
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db.models import Q



class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class ActiveManager(models.Manager):
    """Default manager: only non-archived rows."""
    def get_queryset(self):
        return super().get_queryset().filter(archived_at__isnull=True)

    # Convenience passthroughs
    def active(self):
        return self.get_queryset()

    def archived(self):
        return super().get_queryset().filter(archived_at__isnull=False)
    
class AllObjectsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()


class Audience(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="audiences",
        db_index=True
    )
    description = models.TextField(blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["archived_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                condition=Q(archived_at__isnull=True),
                name="uq_active_audience_user_name",
            ),
            models.UniqueConstraint(
                fields=["user", "slug"],
                condition=Q(archived_at__isnull=True),
                name="uq_active_audience_user_slug",
            ),
        ]

    def __str__(self):
        return f"{self.name} - ({self.slug})"
    
    def _make_unique_slug(self):
        base_slug = slugify(self.name)
        ts = str(time.time()).encode()
        hash_val = hashlib.md5(ts).hexdigest()
        digits = str(int(hash_val, 16))[-4:]  # last 4 digits
        return  f"{base_slug}-{digits}"
    
    def save(self, *args, **kwargs):
        # Only generate if slug is empty or when the name changes on update
        if not self.slug:  
            self.slug = self._make_unique_slug()
        elif self.pk:
            old = type(self).all_objects.only("name").get(pk=self.pk)
            if old.name != self.name:  
                self.slug = self._make_unique_slug()
        super().save(*args, **kwargs)
    
    # Soft delete helpers
    def archive(self, *, by=None):
        """
        Mark as archived.
        """
        if self.archived_at is None:
            self.archived_at = timezone.now()
            self.save(update_fields=["archived_at", "updated_at"])

    def restore(self):
        if self.archived_at is not None:
            self.archived_at = None
            self.save(update_fields=["archived_at", "updated_at"])