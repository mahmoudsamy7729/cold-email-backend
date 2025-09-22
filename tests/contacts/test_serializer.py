import pytest
from contacts.serializers import ContactSerializer
from contacts.models import Contact, ContactStatus

pytestmark = [pytest.mark.django_db]


def test_serializer_strips_and_normalizes(audience, user):
    data = {
        "audience": str(audience.id),
        "email": "  AbC@Email.com  ",
        "first_name": "  Mahmoud  ",
        "last_name": "  Samy ",
        "phone": "",
    }
    s = ContactSerializer(data=data, context={"request": type("Req", (), {"user": user})})
    assert s.is_valid(), s.errors
    obj = s.save()
    assert obj.email == "abc@email.com"
    assert obj.first_name == "Mahmoud"
    assert obj.last_name == "Samy"

def test_uniqueness_same_audience_case_insensitive(audience, user):
    Contact.all_objects.create(audience=audience, email="exists@x.com")
    s = ContactSerializer(data={"audience": str(audience.id), "email": "EXISTS@x.com"},
                           context={"request": type("Req", (), {"user": user})})
    assert not s.is_valid()
    assert "email" in s.errors
    assert s.errors['email'][0] == "This email already exists in this audience."

def test_create_same_email_ignores_archived(audience, user):
    Contact.all_objects.create(audience=audience, email="exists@x.com", status=ContactStatus.ARCHIVED)
    s = ContactSerializer(data={"audience": str(audience.id), "email": "EXISTS@x.com"},
                          context={"request": type("Req", (), {"user": user})})
    assert s.is_valid()
    assert s.validated_data["email"] == "exists@x.com"

def test_create_same_email_different_audinces(audience, other_audience, user, other_user):
    s1 = ContactSerializer(data={
        "audience": str(audience.id),
        "email": "exists@x.com"
    }, context={"request": type("Req", (), {"user": user})})
    assert s1.is_valid()
    c1 = s1.save()
    s2 = ContactSerializer(data={
        "audience": str(other_audience.id),
        "email": "EXISTS@x.com"  # also checks normalization
    }, context={"request": type("Req", (), {"user": other_user})})
    assert s2.is_valid()
    c2 = s2.save()
    assert Contact.all_objects.count() == 2

def test_update_does_not_conflict_with_self(audience, user):
    inst = Contact.all_objects.create(audience=audience, email="me@x.com")
    s = ContactSerializer(instance=inst, data={"email": "ME@x.com"}, partial=True, context={"request": type("Req", (), {"user": user})})
    assert s.is_valid(), s.errors
    obj = s.save()
    assert obj.email == "me@x.com"

    

