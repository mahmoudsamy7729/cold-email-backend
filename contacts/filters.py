from django_filters import rest_framework as filters
from .models import Contact, ContactStatus

class ContactFilter(filters.FilterSet):
    # /api/contacts?tags=vip,owner  -> OR
    tags = filters.CharFilter(method="filter_tags_any")
    status = filters.MultipleChoiceFilter(
        field_name="status",
        choices=ContactStatus.choices,   # validates values
    )

    class Meta:
        model = Contact
        fields = {
            "audience": ["exact"],
        }

    def _parse_csv_tags(self, value: str):
        if not value:
            return []
        return sorted({t.strip().lower() for t in value.split(",") if t.strip()})

    def filter_tags_any(self, qs, name, value):
        tags = self._parse_csv_tags(value)
        return qs if not tags else qs.filter(tags__overlap=tags)