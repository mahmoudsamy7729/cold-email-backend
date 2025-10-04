import uuid
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from campaigns.models import Campaign
from audience.models import Audience
from contacts.models import Contact
from emails.models import Email, EmailStatus

User = get_user_model()


def _seed_campaign_with_email():
    user = User.objects.create_user(username=f"u_{uuid.uuid4().hex[:8]}", password="x", email="u@example.com")
    aud = Audience.objects.create(user=user, name="Scope Audience")
    Contact.objects.create(first_name=user, audience=aud, email=f"lead_{uuid.uuid4().hex[:6]}@example.com")
    camp = Campaign.objects.create(user=user, name=f"Camp_{uuid.uuid4().hex[:5]}")

    e = Email.objects.create(
        campaign=camp,
        audience=aud,
        subject="Scoped Hello",
        content_text="Body",
        from_email="noreply@example.com",
        status=EmailStatus.DRAFT,
    )
    return user, camp, e


def test_list_is_scoped_to_campaign_id(db):
    # Seed two separate campaigns (same user)
    user, camp_a, email_a = _seed_campaign_with_email()
    _, camp_b, email_b = _seed_campaign_with_email()
    # Move second to same user for realism
    camp_b.user = user
    camp_b.save(update_fields=["user"])

    client = APIClient()
    client.force_authenticate(user=user)

    # List A → should only see email_a
    resp_a = client.get(f"/api/campaigns/{camp_a.id}/emails/")
    assert resp_a.status_code == 200
    ids_a = {str(item["id"]) for item in resp_a.json().get("results", resp_a.json())}
    assert str(email_a.id) in ids_a
    assert str(email_b.id) not in ids_a

    # List B → should only see email_b
    resp_b = client.get(f"/api/campaigns/{camp_b.id}/emails/")
    assert resp_b.status_code == 200
    ids_b = {str(item["id"]) for item in resp_b.json().get("results", resp_b.json())}
    assert str(email_b.id) in ids_b
    assert str(email_a.id) not in ids_b
