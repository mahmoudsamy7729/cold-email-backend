from ..models import Contact, ContactStatus, Tag




class DuplicateContactEmail(Exception):
    """Raised when an email already exists in the given audience (case-insensitive)."""

class ContactService:    
    
    @staticmethod
    def ensure_unique_email_in_audience(
        *,
        email: str,
        audience_id: str,
        instance = None,
    ) -> str:
        """
        Ensure `email` is unique (case-insensitive) within a given `audience_id`.
        Returns normalized email or raises DuplicateContactEmail.
        """
        normalized = (email or "").lower()
        qs = Contact.objects.filter(audience_id=audience_id, email=normalized).exclude(status=ContactStatus.ARCHIVED)
        if instance and instance.pk:
            qs = qs.exclude(pk=instance.pk)

        if qs.exists():
            raise DuplicateContactEmail("This email already exists in this audience.")

        return normalized
    

    @staticmethod
    def normalize_tags(tags: list[str]) -> list[str]:
        if not tags:
            return []
        cleaned = {t.strip().lower() for t in tags if isinstance(t, str) and t.strip()}
        return sorted(cleaned)
    
    @staticmethod
    def get_or_create_tags(user, tags):
        existing = set(
            Tag.objects.filter(user=user, name__in=tags).values_list("name", flat=True)
        )
        to_create = [name for name in tags if name not in existing]

        # bulk create missing tags
        Tag.objects.bulk_create(
            [Tag(user=user, name=name) for name in to_create],
            ignore_conflicts=True,  # avoids race condition duplicates
        )
    

