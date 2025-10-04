from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from emails.models import Email
from emails.serializers import EmailSerializer

# we’ll plug this in next step (minimal service entrypoint)
from emails.services.email_services import create_email_draft, PermissionDeniedError
from emails.services.send_service import send_test_email
from django.core.exceptions import ValidationError as DjangoValidationError

from tracking.models import EmailRecipient, RecipientStatus
from tracking.rewrite import rewrite_html_links
from django.core.mail import send_mail, EmailMultiAlternatives
from django.http import JsonResponse
from django.conf import settings
from django.utils.html import escape

class EmailViewSet(viewsets.ModelViewSet):
    serializer_class = EmailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def _campaign_id(self):
        cid = self.kwargs.get("campaign_id")
        if not cid:
            raise NotFound(detail="campaign_id not provided in URL.")
        return cid

    def get_queryset(self):
        campaign_id = self._campaign_id()
        return (
            Email.objects
            .filter(campaign__user=self.request.user, campaign_id=campaign_id)
            .select_related("campaign", "audience")
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["campaign_id"] = self._campaign_id()
        return ctx

    def create(self, request, *args, **kwargs):
        campaign_id = self._campaign_id()

        # 1) validate payload shape using your serializer (no business logic here)
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        # 2) delegate business rules + creation to the service
        try:
            email = create_email_draft(
                user=request.user,
                campaign_id=campaign_id,
                data=ser.validated_data,
            )
        except PermissionDeniedError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except DjangoValidationError as e:
            # e.message_dict is a dict of field -> error(s) if raised like in the service
            detail = getattr(e, "message_dict", None) or {"detail": e.message}
            return Response(detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # unexpected
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 3) serialize the created object back
        out = self.get_serializer(email)
        headers = self.get_success_headers(out.data)
        return Response(out.data, status=status.HTTP_201_CREATED, headers=headers)

    # keep your existing send_test for now; we’ll move it into a service in step 2
    @action(detail=True, methods=["post"], url_path="send-test")
    def send_test(self, request, campaign_id=None, id=None):
        email = self.get_object()
        try:
            result = send_test_email(request=request, user=request.user, email=email)
            return Response(result, status=200)
        except PermissionDeniedError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except DjangoValidationError as e:
            detail = getattr(e, "message_dict", None) or {"detail": e.message}
            return Response(detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

