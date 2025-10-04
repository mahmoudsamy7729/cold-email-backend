import base64
import hmac
import hashlib
from urllib.parse import urlencode, urlparse, urlunparse
from django.conf import settings

HMAC_KEY = settings.SECRET_KEY.encode()

def _urlsafe_b64encode(s: str) -> str:
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")

def _urlsafe_b64decode(s: str) -> str:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode()).decode()

def make_signature(r: str, u: str) -> str:
    """HMAC over 'r|u' (recipient uuid + original url)."""
    msg = f"{r}|{u}".encode()
    digest = hmac.new(HMAC_KEY, msg, hashlib.sha256).hexdigest()
    # keep it short; 24–32 hex chars is typically enough. Use full digest if you prefer.
    return digest[:32]

def verify_signature(r: str, u: str, s: str) -> bool:
    expected = make_signature(r, u)
    return hmac.compare_digest(expected, s)

def build_click_url(request, recipient_id: str, original_url: str) -> str:
    """Construct /t/c?r=<uuid>&u=<b64url>&s=<sig> absolute URL."""
    u_enc = _urlsafe_b64encode(original_url)
    sig = make_signature(recipient_id, original_url)
    query = urlencode({"r": recipient_id, "u": u_enc, "s": sig})
    # Build absolute URL using current host/proto
    scheme = "https" if request.is_secure() else "http"
    netloc = request.get_host()
    path = "/t/c"
    return urlunparse((scheme, netloc, path, "", query, ""))

def build_unsubscribe_url(request, recipient_id: str) -> str:
    """One-click unsubscribe URL that doesn’t need original URL."""
    # We still sign against a fixed 'u' string to keep format uniform.
    original_url = "UNSUB"
    u_enc = _urlsafe_b64encode(original_url)
    sig = make_signature(recipient_id, original_url)
    query = urlencode({"r": recipient_id, "u": u_enc, "s": sig})
    scheme = "https" if request.is_secure() else "http"
    netloc = request.get_host()
    path = "/t/u"
    return urlunparse((scheme, netloc, path, "", query, ""))

def decode_tracked_url(u_enc: str) -> str:
    return _urlsafe_b64decode(u_enc)

