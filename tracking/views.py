from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.utils import timezone
from django.views import View
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from tracking.models import EmailRecipient, TrackEvent, RecipientStatus
from tracking.utils import verify_signature, decode_tracked_url


SAFE_REDIRECT_SCHEMES = {"http", "https"}

def _is_safe_redirect(url: str) -> bool:
    try:
        URLValidator(schemes=list(SAFE_REDIRECT_SCHEMES))(url)
        return True
    except ValidationError:
        return False
    

class ClickRedirectView(View):
    """GET /t/c?r=<uuid>&u=<b64url>&s=<sig>"""
    def get(self, request):
        r = request.GET.get("r")
        u_enc = request.GET.get("u")
        s = request.GET.get("s")
        if not r or not u_enc or not s:
            return JsonResponse({"detail": "Missing parameters."}, status=400)

        try:
            original_url = decode_tracked_url(u_enc)
        except Exception:
            return JsonResponse({"detail": "Invalid URL encoding."}, status=400)

        if not verify_signature(r, original_url, s):
            return JsonResponse({"detail": "Invalid signature."}, status=400)

        if not _is_safe_redirect(original_url):
            return JsonResponse({"detail": "Unsafe redirect target."}, status=400)

        recipient = get_object_or_404(EmailRecipient, id=r)

        with transaction.atomic():
            # Log event
            TrackEvent.objects.create(
                recipient=recipient,
                event_type=RecipientStatus.CLICKED,
                occurred_at=timezone.now(),
                metadata={"url": original_url},
            )
            # Update latest status + last_event_at
            recipient.status = RecipientStatus.CLICKED
            recipient.last_event_at = timezone.now()
            recipient.save(update_fields=["status", "last_event_at", "updated_at"])

        return HttpResponseRedirect(original_url)
    
class UnsubscribeView(View):
    """GET /t/u?r=<uuid>&u=<b64('UNSUB')>&s=<sig>"""
    def get(self, request):
        r = request.GET.get("r")
        u_enc = request.GET.get("u")
        s = request.GET.get("s")
        if not r or not u_enc or not s:
            return JsonResponse({"detail": "Missing parameters."}, status=400)

        try:
            marker = decode_tracked_url(u_enc)
        except Exception:
            return JsonResponse({"detail": "Invalid URL encoding."}, status=400)

        if marker != "UNSUB" or not verify_signature(r, marker, s):
            return JsonResponse({"detail": "Invalid signature."}, status=400)

        recipient = get_object_or_404(EmailRecipient, id=r)

        with transaction.atomic():
            # Log event
            TrackEvent.objects.create(
                recipient=recipient,
                event_type=RecipientStatus.UNSUBSCRIBED,
                occurred_at=timezone.now(),
                metadata={},
            )
            # Update recipient status
            recipient.status = RecipientStatus.UNSUBSCRIBED
            recipient.last_event_at = timezone.now()
            recipient.save(update_fields=["status", "last_event_at", "updated_at"])

            # Apply global suppression (hook point)
            _apply_global_suppression(recipient)

        # Simple confirmation page (you can brand this later)
        return HttpResponse(
            "<!doctype html><meta charset='utf-8'><title>Unsubscribed</title>"
            "<div style='font-family:system-ui;margin:40px;'>"
            "<h1>You’re unsubscribed</h1>"
            "<p>You won’t receive further emails from this sender.</p>"
            "</div>",
            content_type="text/html; charset=utf-8",
        )

def _apply_global_suppression(recipient: EmailRecipient) -> None:
    """
    Hook: mark the contact as globally unsubscribed/suppressed.
    Integrate with your suppressions list or Contact model flag here.
    """
    try:
        contact = recipient.contact
        # Example if you have a boolean on Contact:
        contact.status = "unsubscribed"
        contact.save(update_fields=["status"])
        # If you have a Suppression model, create/update it here instead.
    except Exception:
        # Don’t fail the unsubscribe path if suppression write fails; log it.
        pass