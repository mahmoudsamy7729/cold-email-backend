import pytest

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