from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import Contact, ContactStatus
from .serializers import ContactSerializer


class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    filterset_fields = {
        "audience": ["exact"],
        "status": ["exact"],
    }
    search_fields = ["email", "first_name", "last_name", "phone"]
    ordering_fields = ["created_at", "updated_at", "email", "first_name", "last_name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Contact.objects.filter(audience__user=self.request.user)

    def perform_destroy(self, instance):
        instance.archive()
    
