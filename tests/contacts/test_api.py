import pytest
from django.urls import reverse
from contacts.models import Contact, ContactStatus

pytestmark = [pytest.mark.django_db]

CONTACTS_URL = reverse("contacts:contact-list")


def test_auth_required(api_client):
    r = api_client.get(CONTACTS_URL)
    assert r.status_code == 403

def test_auth_required_for_details(api_client):
    contact_id = "some-id"
    r = api_client.get(f"{CONTACTS_URL}{contact_id}/")
    assert r.status_code == 403

def test_create_contact(auth_client, get_token, user, audience, skip_if_404):
    token = get_token(username=user.username, password="pass1234")
    client = auth_client(token)
    payload = {"email":"test@gmail.com", "audience": audience.id}
    res = client.post(CONTACTS_URL, payload, format="json")
    skip_if_404(res)
    assert res.status_code == 201
    assert res.data['email'] == "test@gmail.com"
    assert res.data['audience'] == audience.id

def test_create_contact_case_senstive(auth_client, get_token, user, audience, create_contact):
    token = get_token(username=user.username, password="pass1234")
    client = auth_client(token)

    create_contact(client, audience, email="test@gmail.com")
    res = create_contact(client, audience, email="TEST@gmail.com")
    
    assert res.status_code == 400
    assert res.data['email'][0] == "This email already exists in this audience."

def test_create_contact_with_audience_of_other_user(auth_client, get_token, user,  other_audience, create_contact):
    token = get_token(username=user.username, password="pass1234")
    client = auth_client(token)
    res = create_contact(client, other_audience, email="TEST@gmail.com")
    assert res.status_code == 400
    assert res.data['audience'][0] == "No audience found for this id."

def test_list_contacts_related_to_user(auth_client, get_token, user, other_user, audience, other_audience, create_contact):
    token1 = get_token(username=user.username, password="pass1234")
    client = auth_client(token1)
    create_contact(client, audience, email="test@gmail.com")

    token2 = get_token(username=other_user.username, password="pass1234")
    client = auth_client(token2)
    create_contact(client, other_audience, email="abc@gmail.com")

    res = client.get(CONTACTS_URL)
    assert res.status_code == 200
    emails = [c["email"] for c in res.data['results']]
    assert "abc@gmail.com" in emails 
    assert "test@gmail.com" not in emails

def test_delete_contact(auth_client, get_token, user, audience, create_contact):
    token = get_token(username=user.username, password="pass1234")
    client = auth_client(token)
    res = create_contact(client, audience, email="test@gmail.com")
    contact_id =  res.data["id"]

    url = f"{CONTACTS_URL}{contact_id}/"
    res = client.delete(url)

    assert res.status_code == 204
    assert not Contact.objects.filter(id=contact_id).exists()
    assert Contact.all_objects.get(id=contact_id).status == ContactStatus.ARCHIVED

def test_update_contact(auth_client, get_token, user, audience, create_contact):
    token = get_token(username=user.username, password="pass1234")
    client = auth_client(token)
    res = create_contact(client, audience, email="test@gmail.com")
    contact_id =  res.data["id"]

    res = client.patch(f"{CONTACTS_URL}{contact_id}/", {"first_name": "Updated"}, format="json")
    contact = Contact.objects.get(id=contact_id)
    assert res.status_code == 200
    assert contact.first_name == "Updated"
    assert contact.email == "test@gmail.com"

def test_update_contact_to_other_user_audience(auth_client, get_token, user, audience, other_audience, create_contact):
    token = get_token(username=user.username, password="pass1234")
    client = auth_client(token)
    c1 = create_contact(client, audience, email="test@gmail.com")
    contact_id = c1.data['id']

    res = client.patch(f"{CONTACTS_URL}{contact_id}/", {"audience": other_audience.id}, format="json")
    assert res.status_code == 400
    assert res.data['audience'][0] == "No audience found for this id."

def test_update_contact_not_allowed(auth_client, get_token, user, audience, create_contact):
    token = get_token(username=user.username, password="pass1234")
    client = auth_client(token)
    c1 = create_contact(client, audience, email="test@gmail.com")

    c2 = create_contact(client, audience, email="ABC@gmail.com")
    contact_id =  c2.data["id"]

    res = client.patch(f"{CONTACTS_URL}{contact_id}/", {"email": "test@gmail.com"}, format="json")
    assert res.status_code == 400
    assert res.data['email'][0] == "This email already exists in this audience."

def test_retrive_active_contacts(auth_client, get_token, user, audience, create_contact):
    token = get_token(username=user.username, password="pass1234")
    client = auth_client(token)
    c1 = create_contact(client, audience, email="test@gmail.com")

    c2 = create_contact(client, audience, email="ABC@gmail.com")

    contact_id = c1.data['id']
    client.delete(f"{CONTACTS_URL}{contact_id}/")    

    res = client.get(CONTACTS_URL)
    assert res.status_code == 200
    emails = [c["email"] for c in res.data['results']]
    assert "abc@gmail.com" in emails 
    assert "test@gmail.com" not in emails

def test_retrive_not_owned_contact(auth_client, get_token, user, other_user, audience, other_audience, create_contact):
    token1 = get_token(username=user.username, password="pass1234")
    client = auth_client(token1)
    c1 = create_contact(client, audience, email="test@gmail.com")

    token2 = get_token(username=other_user.username, password="pass1234")
    client = auth_client(token2)
    c2 = create_contact(client, other_audience, email="ABC@gmail.com")
    contact_id = c1.data['id']

    res = client.get(f"{CONTACTS_URL}{contact_id}/")
    assert res.status_code == 404

def test_create_contact_with_tags(auth_client, audience, get_token, user):
    token1 = get_token(username=user.username, password="pass1234")
    client = auth_client(token1)
    payload = {
        "audience": str(audience.id),
        "email": "a@x.com",
        "tags": ["Dev", "DEV", " Backend  ", "backend"]
    }
    resp = client.post(CONTACTS_URL, payload, format="json")
    assert resp.status_code == 201
    data = resp.json()
    assert sorted(data["tags"]) == ["backend", "dev"]

def test_update_contact_replaces_tags(auth_client, audience, get_token, user):
    token1 = get_token(username=user.username, password="pass1234")
    client = auth_client(token1)
    payload = {
        "audience": str(audience.id),
        "email": "a@x.com",
        "tags": ["dev", "backend"]
    }
    resp = client.post(CONTACTS_URL, payload, format="json")
    resp = client.patch(f"{CONTACTS_URL}{resp.data['id']}/", {"tags": ["sales"]}, format="json")
    assert resp.status_code == 200
    assert sorted(resp.data["tags"]) == ["sales"]

def test_filter_contacts_by_tags_overlap(auth_client, audience, get_token, user):
    token1 = get_token(username=user.username, password="pass1234")
    client = auth_client(token1)

    payload = {
        "audience": str(audience.id),
        "email": "a@x.com",
        "tags": ["dev", "backend"]
    }
    C1 = client.post(CONTACTS_URL, payload, format="json")

    payload = {
        "audience": str(audience.id),
        "email": "a@x.com",
        "tags": ["sales"]
    }
    C2 = client.post(CONTACTS_URL, payload, format="json")

    res = client.get(CONTACTS_URL, {"tags": "dev,unknown"})
    assert res.status_code == 200
    assert len(res.data['results']) == 1
    assert res.data['results'][0]['id'] == C1.data['id']










