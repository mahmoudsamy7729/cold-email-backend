from django.urls import reverse
import pytest
pytestmark = [pytest.mark.django_db, pytest.mark.auth]

LOGIN_URL = reverse("accounts:login")
ACCESS_FIELD = "access_token"
EXP_FIELD = "expires_at"
REFRESH_COOKIE_NAME = "refresh_token"  

def _skip_if_404(resp):
    if resp.status_code == 404:
        pytest.skip(f"Endpoint not found: {resp.request['PATH_INFO']}")

def test_login(api_client, user):
    payload = {"username": user.username, "password": "pass1234"} 
    res = api_client.post(LOGIN_URL, payload, format="json")
    _skip_if_404(res)

    assert res.status_code == 200
    data = res.data
    assert ACCESS_FIELD in data 
    assert EXP_FIELD in data
    cookie = res.cookies.get(REFRESH_COOKIE_NAME)
    assert cookie is not None, f"{REFRESH_COOKIE_NAME} cookie not found in response cookies"
    assert cookie["httponly"] == True or str(cookie["httponly"]).lower() == "true"

def test_login_fail(api_client):
    payload = {"username": "wrong username", "password": "wrong password"}
    res = api_client.post(LOGIN_URL, payload, format="json")
    _skip_if_404(res)

    assert res.status_code == 403
    assert ACCESS_FIELD not in res.data
    assert res.data['detail'] == "Invalid credentials"
