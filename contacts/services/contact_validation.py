from ..models import Contact, ContactStatus



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
    

