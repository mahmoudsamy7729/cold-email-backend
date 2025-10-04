import uuid
import pytest
from django.urls import reverse


LOGIN_URL = reverse("accounts:login")
REGISTER_URL = reverse("accounts:register")
CONTACTS_URL = reverse("contacts:contact-list")
ACCESS_FIELD = "access_token"


@pytest.fixture
def skip_if_404():
    def _skip(resp):
        if resp.status_code == 404:
            pytest.skip(f"Endpoint not found: {resp.request['PATH_INFO']}")
    return _skip

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username="tester",
        email="tester@example.com",
        password="pass1234",
    )

@pytest.fixture
def other_user(django_user_model):
    return django_user_model.objects.create_user(
        username="other",
        email="other@example.com",
        password="pass1234",
    )



@pytest.fixture
def get_token(api_client):
    """Return a function to fetch a token for register/login."""
    def _get_token(username, password, email=None):
        if email:  # register
            payload = {"username": username, "email": email, "password": password}
            res = api_client.post(REGISTER_URL, payload, format="json")
            assert res.status_code == 201
            return res.data[ACCESS_FIELD]

        # login
        payload = {"username": username, "password": password}
        res = api_client.post(LOGIN_URL, payload, format="json")
        assert res.status_code == 200, res.data
        return res.data[ACCESS_FIELD]

    return _get_token

@pytest.fixture
def auth_client(api_client):
    """Return a function that sets token and returns an authenticated client."""
    def _auth_client(token):
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return api_client
    return _auth_client


@pytest.fixture
def audience_model():
    from audience.models import Audience
    return Audience

@pytest.fixture
def audience(db, audience_model, user):
    """Default audience for the authenticated user"""
    return audience_model.objects.create(
        id=uuid.uuid4(),
        user=user,
        name="Test Audience",
    )


@pytest.fixture
def other_audience(db, audience_model, other_user):
    """Audience belonging to another user (should be excluded from queryset)"""
    return audience_model.objects.create(
        id=uuid.uuid4(),
        user=other_user,
        name="Other Audience",
    )


@pytest.fixture
def create_contact():
    """Factory to create a contact with given client, audience, and email."""
    def _create_contact(client, audience, email="test@gmail.com"):
        payload = {"email": email, "audience": audience.id}
        return client.post(CONTACTS_URL, payload, format="json")
    return _create_contact

@pytest.fixture
def campagin_model():
    from campaigns.models import Campaign
    return Campaign

@pytest.fixture
def campaign(db, campagin_model, user):
    """Default campaign for the authenticated user"""
    return campagin_model.objects.create(
        id=uuid.uuid4(),
        user=user,
        name="Test Campagin",
    )


@pytest.fixture
def other_campaign(db, campaign_model, other_user):
    """campaign belonging to another user (should be excluded from queryset)"""
    return campaign_model.objects.create(
        id=uuid.uuid4(),
        user=other_user,
        name="Other Campaign",
    )




def get_emails_url(campaign_id):
    return reverse(
        "emails:email-list-create",  
        kwargs={
            "campaign_id": campaign_id,
        }
    )

@pytest.fixture
def emails_model():
    from emails.models import Email
    return Email

@pytest.fixture
def create_email(api_client, auth_client, get_token, user, campaign, audience):
    """
    Factory to create an Email via API for the authenticated 'user'.
    Returns (client, response), where client is already authenticated.
    """
    def _create_email(*, subject="Hello", content_text="Body", from_email="me@test.com", audience_id=None):
        token = get_token(user.username, "pass1234")
        client = auth_client(token)
        payload = {
            "audience": str(audience_id or audience.id),
            "subject": subject,
            "content_text": content_text,
            "from_email": from_email,
        }
        
        url = get_emails_url(campaign.id)
        res = client.post(url, payload, format="json")
        return client, res
    return _create_email


@pytest.fixture
def create_contact_for_audience(api_client, auth_client, get_token, user):
    """
    Factory to create a contact into a given audience for the authenticated 'user'.
    """
    def _create_contact_for_audience(audience, email="test1@example.com"):
        token = get_token(user.username, "pass1234")
        client = auth_client(token)
        payload = {"email": email, "audience": str(audience.id)}
        res = client.post(CONTACTS_URL, payload, format="json")
        return client, res
    return _create_contact_for_audience

@pytest.fixture
def email_ready_to_test(create_contact_for_audience, create_email, audience):
    """
    Returns (client, campaign_id, email_id) where audience has 1 contact with an email.
    """
    _, c_res = create_contact_for_audience(audience, email="rcpt@example.com")
    assert c_res.status_code in (200, 201)
    client, e_res = create_email(audience_id=audience.id)
    assert e_res.status_code == 201
    from campaigns.models import Campaign
    # campaign used inside create_email comes from the fixture, so return it too
    # But create_email closes over 'campaign' fixture; easiest is to just pass back what tests already have
    return client, e_res.data["id"]