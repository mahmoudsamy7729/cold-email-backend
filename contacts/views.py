from django.shortcuts import get_object_or_404
from django.db.models import Q
from contacts.services.contact_service import ContactService
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ContactFilter

from .models import Contact
from .serializers import ContactSerializer
from contacts.cache_utils import invalidate



class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    filterset_class = ContactFilter
    search_fields = ["email", "first_name", "last_name", "phone"]
    ordering_fields = ["created_at", "updated_at", "email", "first_name", "last_name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Contact.objects.filter(audience__user=self.request.user).select_related('audience').all()
    
    def list(self, request, *args, **kwargs):
        params = set(request.query_params.keys())
        if params - {"page"}:
            invalidate(self.request.user.id)

        queryset = self.filter_queryset(self.get_queryset())
        service = ContactService(request.user)
        data = service.get_contacts(queryset, search=request.query_params.get("search"))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def perform_destroy(self, instance):
        obj = instance.archive()
        invalidate(self.request.user.id)

    def perform_create(self, serializer):
        obj = serializer.save()
        invalidate(self.request.user.id)

    
    
