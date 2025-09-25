from audience.cache_utils import get_cached, set_cached
from audience.models import Audience
from audience.serializers import AudienceSerializer
from django.db.models import Q, Count
from contacts.models import ContactStatus
class AudienceService:
    def __init__(self, user):
        self.user = user

    def get_audiences(self, search=None):
        cached = get_cached(self.user.id)
        if cached is not None:
            if search:
                return [
                    item for item in cached
                    if search.lower() in str(item).lower()
                ]
            return cached

        # fetch from DB if no cache
        qs = Audience.objects.filter(user=self.user).annotate(
            contacts_count=Count("contacts", ~Q(contacts__status=ContactStatus.ARCHIVED))
        )
        serializer = AudienceSerializer(qs, many=True)
        data = serializer.data
        set_cached(self.user.id, data)
        return data
