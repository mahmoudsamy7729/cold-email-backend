from django.core.cache import cache


KEY_PREFIX = "user_contacts"

def contacts_key(user_id: int | str) -> str:
    return f"{KEY_PREFIX}:{user_id}"

def get_cached(user_id):
    return cache.get(contacts_key(user_id))

def set_cached(user_id, data):
    # no TTL: we’ll invalidate on CRUD
    cache.set(contacts_key(user_id), data)

def invalidate(user_id):
    cache.delete(contacts_key(user_id))
    
