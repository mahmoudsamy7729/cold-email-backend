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