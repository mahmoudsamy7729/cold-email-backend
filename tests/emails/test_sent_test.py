import pytest
from django.core import mail
from django.urls import NoReverseMatch, reverse


pytestmark = pytest.mark.django_db


def get_send_test_url(campaign_id, email_id):
    return reverse(
        "emails:email-send-test",  
        kwargs={
            "campaign_id": campaign_id,
            "id": email_id,
        }
    )

def get_email_detial_url(campaign_id, email_id):
    return reverse(
        "emails:email-detail",  
        kwargs={
            "campaign_id": campaign_id,
            "id": email_id,
        }
    )

def test_create_email_and_send_test_success(
    create_email,
    create_contact_for_audience,
    audience,
    campaign,
):
    # Ensure there is at least one contact in the audience
    _, c_res = create_contact_for_audience(audience, email="rcpt@example.com")
    assert c_res.status_code in (200, 201), c_res.data if hasattr(c_res, "data") else c_res.content

    client, e_res = create_email(
        subject="Subject",
        content_text="Hello world",
        from_email="sender@example.com",
        audience_id=audience.id,
    )
    assert e_res.status_code == 201, e_res.data
    email_id = e_res.data["id"]

    # send-test endpoint
    url = get_send_test_url(campaign.id, email_id)
    res = client.post(url, {}, format="json")
    assert res.status_code == 200, res.data
    assert res.data["status"] == "sent"
    assert res.data["to"] == "rcpt@example.com"

    # using locmem backend, verify one message was sent
    assert len(mail.outbox) == 1
    msg = mail.outbox[0]
    assert msg.subject == "Subject"
    assert "Hello world" in msg.body
    assert "rcpt@example.com" in msg.to


def test_send_test_requires_audience_with_contact(
    create_email,
    campaign,
):
    # No contact created in audience -> should 400
    client, e_res = create_email()
    assert e_res.status_code == 201
    email_id = e_res.data["id"]


    url = get_send_test_url(campaign.id, email_id)
    res = client.post(url, {}, format="json")
    assert res.status_code == 400
    assert "Audience has no contacts" in str(res.data)

def test_send_test_forbidden_on_other_users_email(
    api_client,
    auth_client,
    get_token,
    user,
    other_user,
    audience_model,
    campagin_model,
):
    other_campaign = campagin_model.objects.create(user=other_user, name="O Campaign")
    other_audience = audience_model.objects.create(user=other_user, name="O Audience")

    from emails.models import Email
    other_email = Email.objects.create(
        campaign=other_campaign,
        audience=other_audience,
        subject="X",
        content_text="Y",
        from_email="z@x.com",
    )

    # Login as a *different* user
    token = get_token(user.username, "pass1234")
    client = auth_client(token)

    url = get_send_test_url(other_campaign.id, other_email.id)
    res = client.post(url, {}, format="json")

    # Our view/service returns 403 on PermissionDeniedError
    assert res.status_code in (403, 404), res.data 


