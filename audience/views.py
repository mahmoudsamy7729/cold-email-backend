from django.db import IntegrityError
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.db.models import Count, Q
from contacts.models import ContactStatus

from .models import Audience
from .serializers import AudienceSerializer


class AudienceViewSet(viewsets.ModelViewSet):
    serializer_class = AudienceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "slug", "description"]
    ordering_fields = ["updated_at", "created_at", "name"]

    def get_queryset(self):
        return Audience.objects.filter(user=self.request.user).annotate(contacts_count=Count("contacts",~Q(contacts__status=ContactStatus.ARCHIVED)))
    
    def perform_destroy(self, instance):
        instance.archive()

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError:
            raise ValidationError("You already have an active audience with this name.")
        
    def perform_update(self, serializer):
        try:
            serializer.save()
        except IntegrityError:
            raise ValidationError("You already have an active audience with this name.")
