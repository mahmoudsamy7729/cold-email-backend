from django.urls import reverse
import pytest
pytestmark = [pytest.mark.django_db, pytest.mark.auth]


PROFILE_URL = reverse("accounts:profile")    
REGISTER_URL = reverse("accounts:register") 

def test_profile_requires_auth(api_client, skip_if_404):

    res = api_client.get(PROFILE_URL)
    skip_if_404(res)
    assert res.status_code == 403


    paylod = {"username": "tester",
        "email": "tester@example.com",
     "password": "pass1234"}
    
    res = api_client.post(REGISTER_URL, paylod, format="json")
    skip_if_404(res)
    assert res.status_code == 201
    assert "access_token" in res.data
    assert "expires_at" in res.data
    assert "refresh_token" in res.cookies
    
    access_token = res.data["access_token"]

    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    res = api_client.get(PROFILE_URL)
    assert res.status_code == 200
    assert res.data['user'] == "tester"
    assert res.data['email'] == "tester@example.com"
