from django.db import IntegrityError
from audience.services.audience_service import AudienceService
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.db.models import Q, Count
from audience.cache_utils import invalidate


from contacts.models import ContactStatus
from .models import Audience
from .serializers import AudienceSerializer



class AudienceViewSet(viewsets.ModelViewSet):
    serializer_class = AudienceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["updated_at", "created_at", "name"]
    ordering = ["-created_at"] 

    def get_queryset(self):
        return Audience.objects.filter(user=self.request.user).annotate(contacts_count=Count("contacts",~Q(contacts__status=ContactStatus.ARCHIVED)))
    
    def list(self, request, *args, **kwargs):
        service = AudienceService(request.user)
        data = service.get_audiences(search=request.query_params.get("search"))
        page = self.paginate_queryset(self.get_queryset())
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)
    
    def perform_destroy(self, instance):
        instance.archive()
        invalidate(self.request.user.id)

    def perform_create(self, serializer):
        try:
            serializer.save()
            invalidate(self.request.user.id)
        except IntegrityError:
            raise ValidationError("You already have an active audience with this name.")
        
    def perform_update(self, serializer):
        try:
            serializer.save()
            invalidate(self.request.user.id)
        except IntegrityError:
            raise ValidationError("You already have an active audience with this name.")
