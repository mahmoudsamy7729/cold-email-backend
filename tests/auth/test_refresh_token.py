from django.urls import reverse
import pytest
pytestmark = [pytest.mark.django_db, pytest.mark.auth]

LOGIN_URL = reverse("accounts:login")                  
REFRESH_URL = reverse("accounts:refresh-token")        
REFRESH_COOKIE_NAME = "refresh_token"

def test_refresh_uses_cookie_to_issue_new_access(api_client, user, skip_if_404):
    payload = {"username": user.username, "password": "pass1234"} 
    res = api_client.post(LOGIN_URL, payload, format="json")
    skip_if_404(res)
    
    assert res.status_code == 200
    cookie = res.cookies.get(REFRESH_COOKIE_NAME)
    assert cookie is not None, f"{REFRESH_COOKIE_NAME} cookie not found after login"

    api_client.cookies[REFRESH_COOKIE_NAME] = cookie.value

    res = api_client.post(REFRESH_URL, {}, format="json")
    skip_if_404(res)
    assert res.status_code == 200
    assert "access_token" in res.data
    assert "expires_at" in res.data

def test_refresh_token_missing(api_client, user, skip_if_404):
    payload = {"username": user.username, "password": "pass1234"} 
    res = api_client.post(LOGIN_URL, payload, format="json")
    skip_if_404(res)
    
    assert res.status_code == 200
    
    del api_client.cookies[REFRESH_COOKIE_NAME]
    res = api_client.post(REFRESH_URL, {}, format="json")
    skip_if_404(res)
    assert res.status_code == 403
    assert res.data['detail'] == "Refresh token is missing"

def test_refresh_token_invalid(api_client, user, skip_if_404):
    payload = {"username": user.username, "password": "pass1234"}
    res = api_client.post(LOGIN_URL, payload, format="json")
    skip_if_404(res)

    assert res.status_code == 200

    api_client.cookies[REFRESH_COOKIE_NAME] = "invalid token"
    res = api_client.post(REFRESH_URL, {}, format="json")
    skip_if_404(res)
    assert res.status_code == 403
    assert res.data['detail'] == "Invalid refresh token"


def test_refresh_token_for_deleted_user(api_client, user, skip_if_404):
    payload = {"username": user.username, "password": "pass1234"}
    res = api_client.post(LOGIN_URL, payload, format="json")
    skip_if_404(res)

    assert res.status_code == 200
    cookie = res.cookies.get(REFRESH_COOKIE_NAME)
    assert cookie is not None, f"{REFRESH_COOKIE_NAME} cookie not found after login"

    api_client.cookies[REFRESH_COOKIE_NAME] = cookie.value
    user.delete()

    res = api_client.post(REFRESH_URL, {}, format="json")
    skip_if_404(res)
    assert res.status_code == 403
    assert res.data['detail'] == "Invalid refresh token"

