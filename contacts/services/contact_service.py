from contacts.models import Contact
from contacts.serializers import ContactSerializer
from contacts.cache_utils import get_cached, set_cached

class ContactService:
    def __init__(self, user):
        self.user = user

    def get_contacts(self, queryset, search=None):
        cached = get_cached(self.user.id)
        if cached is not None:
            if search:
                return [
                    item for item in cached
                    if search.lower() in str(item).lower()
                ]
            return cached

        # No cache → use queryset provided by the viewset
        serializer = ContactSerializer(queryset, many=True)
        data = serializer.data
        set_cached(self.user.id, data)
        return data