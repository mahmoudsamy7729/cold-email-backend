import django_filters
from .models import Campaign, CampaignStatus, ScheduleType

class CharInFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    """Accepts ?status=draft,paused or ?status=draft&status=paused."""
    pass

class CampaignFilter(django_filters.FilterSet):
    # Multiple statuses and schedule types
    status = CharInFilter(field_name="status", lookup_expr="in")
    schedule_type = CharInFilter(field_name="schedule_type", lookup_expr="in")

    # Optional date/time range filters for scheduled campaigns
    scheduled_from = django_filters.IsoDateTimeFilter(field_name="scheduled_at", lookup_expr="gte")
    scheduled_to   = django_filters.IsoDateTimeFilter(field_name="scheduled_at", lookup_expr="lte")

    class Meta:
        model = Campaign
        fields = ["status", "schedule_type", "scheduled_from", "scheduled_to"]
