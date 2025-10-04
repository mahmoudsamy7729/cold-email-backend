# tests/tracking/test_tracking_endpoints.py
import uuid
from django.test import RequestFactory
from django.utils import timezone
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from campaigns.models import Campaign
from audience.models import Audience
from contacts.models import Contact
from emails.models import Email, EmailStatus
from tracking.models import EmailRecipient, RecipientStatus, TrackEvent
from tracking.utils import build_click_url, build_unsubscribe_url, make_signature, _urlsafe_b64encode

User = get_user_model()


def _seed(minimal=False):
    user = User.objects.create_user(username=f"u_{uuid.uuid4().hex[:8]}", password="x", email="u@example.com")
    aud = Audience.objects.create(user=user, name="Test Audience")
    contact = Contact.objects.create(first_name=user, audience=aud, email=f"lead_{uuid.uuid4().hex[:6]}@example.com")
    camp = Campaign.objects.create(user=user, name="Test Campaign")
    email = Email.objects.create(
        campaign=camp,
        audience=aud,
        subject="Hello",
        content_text="Hi there",
        from_email="noreply@example.com",
        status=EmailStatus.DRAFT,
        scheduled_at=None,
    )
    recipient = EmailRecipient.objects.create(
        email=email,
        contact=contact,
        status=RecipientStatus.QUEUED,
        last_event_at=None,
    )
    return user, aud, contact, camp, email, recipient


def _request_with_host():
    rf = RequestFactory()
    # IMPORTANT: Set host so build_* creates absolute URLs (the client accepts absolute URLs)
    return rf.get("/", HTTP_HOST="testserver")


def test_click_redirect_updates_status_and_logs_event(db):
    user, aud, contact, camp, email, recipient = _seed()
    req = _request_with_host()
    target = "https://example.com/landing"
    click_url = build_click_url(req, str(recipient.id), target)

    client = APIClient()
    # public endpoint, no auth
    resp = client.get(click_url, follow=False)

    assert resp.status_code == 302
    assert resp["Location"] == target

    recipient.refresh_from_db()
    assert recipient.status == RecipientStatus.CLICKED
    assert recipient.last_event_at is not None

    ev = TrackEvent.objects.filter(recipient=recipient, event_type=RecipientStatus.CLICKED).first()
    assert ev is not None
    assert ev.metadata.get("url") == target


def test_unsubscribe_updates_status_and_logs_event(db):
    user, aud, contact, camp, email, recipient = _seed()
    req = _request_with_host()
    unsub_url = build_unsubscribe_url(req, str(recipient.id))

    client = APIClient()
    resp = client.get(unsub_url, follow=False)

    assert resp.status_code == 200
    recipient.refresh_from_db()
    assert recipient.status == RecipientStatus.UNSUBSCRIBED

    ev = TrackEvent.objects.filter(recipient=recipient, event_type=RecipientStatus.UNSUBSCRIBED).first()
    assert ev is not None


def test_invalid_signature_returns_400_and_no_state_change(db):
    user, aud, contact, camp, email, recipient = _seed()
    # Manually craft a tampered click URL (wrong signature)
    req = _request_with_host()
    bad_target = "https://example.com/tampered"
    u_enc = _urlsafe_b64encode(bad_target)
    # WRONG signature on purpose
    bad_sig = "deadbeef" * 4
    url = f"/t/c?r={recipient.id}&u={u_enc}&s={bad_sig}"

    client = APIClient()
    resp = client.get(url, follow=False)
    assert resp.status_code == 400

    recipient.refresh_from_db()
    # Status unchanged
    assert recipient.status == RecipientStatus.QUEUED
    assert not TrackEvent.objects.filter(recipient=recipient).exists()
