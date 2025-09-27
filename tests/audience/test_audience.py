import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from audience.models import Audience

pytestmark = [pytest.mark.django_db, pytest.mark.auth]

AUDIENCE_URL = reverse("audience:audience-list")

def test_unauthorized_create_audience(api_client, skip_if_404):
    payload = {"name":"Test Audience"}
    response = api_client.post(AUDIENCE_URL, payload)
    skip_if_404(response)
    assert response.status_code == 403

def test_create_empty_audience_name(auth_client, get_token, user, skip_if_404):
    token = get_token(username = user.username, password = "pass1234")
    client = auth_client(token)
    payload = {"name":""}
    response = client.post(AUDIENCE_URL, payload)
    skip_if_404(response)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["name"][0] == "This field may not be blank."

def test_create_audience(auth_client, get_token, user, skip_if_404):
    token = get_token(username = user.username, password = "pass1234")
    client = auth_client(token)
    payload = {"name":"Test Audience"}
    response = client.post(AUDIENCE_URL, payload)
    skip_if_404(response)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "Test Audience"

def test_dublicate_name_audience(auth_client, get_token, user, skip_if_404):
    token = get_token(username = user.username, password = "pass1234")
    client = auth_client(token)
    payload = {"name":"Test Audience"}
    response = client.post(AUDIENCE_URL, payload)
    skip_if_404(response)
    payload = {"name":"Test Audience"}
    response = client.post(AUDIENCE_URL, payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["name"][0] == "You already have an active audience with this name."


def test_list_returns_only_user_audiences(auth_client, get_token, user, skip_if_404):
    token1 = get_token(username = "taster1", password = "pass1234", email = "tester11@gmail.com")
    client1 = auth_client(token1)
    payload = {"name":"Audience for user 1"}
    res = client1.post(AUDIENCE_URL, payload)
    skip_if_404(res)
    token2 = get_token(username = user.username, password = "pass1234")
    client2 = auth_client(token2)
    payload = {"name":"Audience for user 2"}
    res = client2.post(AUDIENCE_URL, payload)
    res = client2.get(AUDIENCE_URL)
    skip_if_404(res)
    assert res.status_code == 200 
    names = [a["name"] for a in res.data['results']]
    assert "Audience for user 2" in names
    assert "Audience for user 1" not in names

def test_update_audience_name(auth_client, get_token, user, skip_if_404):
    token = get_token(username=user.username, password="pass1234")
    client = auth_client(token)

    res = client.post(AUDIENCE_URL, {"name": "Original"})
    skip_if_404(res)
    audience_id = res.data["id"]
    res = client.patch(f"{AUDIENCE_URL}{audience_id}/", {"name": "Updated"})
    skip_if_404(res)
    assert res.status_code == 200
    assert res.data["name"] == "Updated"

def test_update_audience_duplicate_name(auth_client, get_token, user, skip_if_404):
    token = get_token(username=user.username, password="pass1234")
    client = auth_client(token)

    res1 = client.post(AUDIENCE_URL, {"name": "First"})
    res2 = client.post(AUDIENCE_URL, {"name": "Second"})

    res = client.patch(f"{AUDIENCE_URL}{res2.data['id']}/", {"name": "First"})
    skip_if_404(res)
    assert res.status_code == 400
    assert res.data["name"][0] == "You already have an active audience with this name."

def test_delete_archives_audience(auth_client, get_token, user, skip_if_404):
    token = get_token(username=user.username, password="pass1234")
    client = auth_client(token)

    res = client.post(AUDIENCE_URL, {"name": "ToDelete"})
    skip_if_404(res)
    audience_id = res.data["id"]

    del_res = client.delete(f"{AUDIENCE_URL}{audience_id}/")
    skip_if_404(del_res)
    assert del_res.status_code == 204

    list_res = client.get(AUDIENCE_URL)
    names = [a["name"] for a in list_res.data['results']]
    assert "ToDelete" not in names

    





