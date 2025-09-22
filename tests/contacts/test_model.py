import pytest
import threading
from queue import Queue
from django.db import IntegrityError, transaction, connections
from django.conf import settings
from contacts.models import Contact, ContactStatus


pytestmark = [pytest.mark.django_db]

def test_manager_excludes_archived(audience):
    c1 = Contact.objects.create(audience= audience, email="c1@x.com")
    c2 = Contact.objects.create(audience=audience, email="c2@x.com")
    c2.archive()

    visible_emails = set(Contact.objects.values_list("email", flat=True))
    assert "c1@x.com" in visible_emails
    assert "c2@x.com" not in visible_emails

def test_unique_email_per_audience_ignores_archived(audience):
    old = Contact.objects.create(audience=audience, email="dup@x.com")
    old.archive()
    # should be allowed while previous archived
    Contact.objects.create(audience=audience, email="dup@x.com")

def test_db_unique_constraint_same_audience_raises_integrity_error(audience):
    Contact.all_objects.create(audience=audience, email="dup@x.com")

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Contact.all_objects.create(audience=audience, email="DUP@x.com")



