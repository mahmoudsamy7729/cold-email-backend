from audience.models import Audience

def test_slug_is_generated(user):
    a = Audience.objects.create(user=user, name="My Audience")
    assert a.slug.startswith("my-audience-")

def test_slug_changes_when_name_changes(user):
    a = Audience.objects.create(user=user, name="Initial")
    old_slug = a.slug
    a.name = "Changed"
    a.save()
    assert a.slug != old_slug
    assert a.slug.startswith("changed-")

def test_archive_and_restore(user):
    a = Audience.objects.create(user=user, name="Archivable")
    assert a.archived_at is None
    a.archive()
    assert a.archived_at is not None
    a.restore()
    assert a.archived_at is None