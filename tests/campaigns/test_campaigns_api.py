import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from campaigns.models import Campaign

pytestmark = [pytest.mark.django_db, pytest.mark.auth]

CAMPAIGN_URL = reverse("campaigns:campaign-list")

def test_unauthorized_create_campaign(api_client, skip_if_404):
    payload = {"name":"Test Campaign"}
    response = api_client.post(CAMPAIGN_URL, payload)
    skip_if_404(response)
    assert response.status_code == 403

def test_create_empty_campaign_name(auth_client, get_token, user, skip_if_404):
    token = get_token(username = user.username, password = "pass1234")
    client = auth_client(token)
    payload = {"name":""}
    response = client.post(CAMPAIGN_URL, payload)
    skip_if_404(response)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["name"][0] == "This field may not be blank."

def test_create_campaign(auth_client, get_token, user, skip_if_404):
    token = get_token(username = user.username, password = "pass1234")
    client = auth_client(token)
    payload = {"name":"Test campaign"}
    response = client.post(CAMPAIGN_URL, payload)
    skip_if_404(response)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "Test campaign"


def test_dublicate_name_campaign(auth_client, get_token, user, skip_if_404):
    token = get_token(username = user.username, password = "pass1234")
    client = auth_client(token)
    payload = {"name":"Test Campaign"}
    response = client.post(CAMPAIGN_URL, payload)
    skip_if_404(response)
    payload = {"name":"Test Campaign"}
    response = client.post(CAMPAIGN_URL, payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["name"][0] == "You already have an active campaign with this name."


def test_list_returns_only_user_audiences(auth_client, get_token, user, skip_if_404):
    token1 = get_token(username = "taster1", password = "pass1234", email = "tester11@gmail.com")
    client1 = auth_client(token1)
    payload = {"name":"Campaign for user 1"}
    res = client1.post(CAMPAIGN_URL, payload)
    skip_if_404(res)
    token2 = get_token(username = user.username, password = "pass1234")
    client2 = auth_client(token2)
    payload = {"name":"Campaign for user 2"}
    res = client2.post(CAMPAIGN_URL, payload)
    res = client2.get(CAMPAIGN_URL)
    skip_if_404(res)
    assert res.status_code == 200 
    names = [a["name"] for a in res.data['results']]
    assert "Campaign for user 2" in names
    assert "Campaign for user 1" not in names

def test_update_audience_name(auth_client, get_token, user, skip_if_404):
    token = get_token(username=user.username, password="pass1234")
    client = auth_client(token)

    res = client.post(CAMPAIGN_URL, {"name": "Original"})
    skip_if_404(res)
    campaign_id = res.data["id"]
    res = client.patch(f"{CAMPAIGN_URL}{campaign_id}/", {"name": "Updated"})
    skip_if_404(res)
    assert res.status_code == 200
    assert res.data["name"] == "Updated"

def test_update_audience_duplicate_name(auth_client, get_token, user, skip_if_404):
    token = get_token(username=user.username, password="pass1234")
    client = auth_client(token)

    res1 = client.post(CAMPAIGN_URL, {"name": "First"})
    res2 = client.post(CAMPAIGN_URL, {"name": "Second"})

    res = client.patch(f"{CAMPAIGN_URL}{res2.data['id']}/", {"name": "First"})
    skip_if_404(res)
    assert res.status_code == 400
    assert res.data["name"][0] == "You already have an active campaign with this name."

def test_delete_archives_audience(auth_client, get_token, user, skip_if_404):
    token = get_token(username=user.username, password="pass1234")
    client = auth_client(token)

    res = client.post(CAMPAIGN_URL, {"name": "ToDelete"})
    skip_if_404(res)
    campaign_id = res.data["id"]

    del_res = client.delete(f"{CAMPAIGN_URL}{campaign_id}/")
    skip_if_404(del_res)
    assert del_res.status_code == 204

    list_res = client.get(CAMPAIGN_URL)
    names = [a["name"] for a in list_res.data['results']]
    assert "ToDelete" not in names