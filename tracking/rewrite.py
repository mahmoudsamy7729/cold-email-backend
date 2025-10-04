import re
from typing import Callable
from django.http import HttpRequest
from tracking.utils import build_click_url, build_unsubscribe_url

HREF_RE = re.compile(r'href=(["\'])(?P<url>.+?)\1', flags=re.IGNORECASE)

def rewrite_html_links(
    request: HttpRequest,
    html: str,
    recipient_id: str,
    unsubscribe_text: str | None = "Unsubscribe",
) -> str:
    """
    Rewrites all hrefs to tracked click URLs and appends an unsubscribe link.
    """

    def _replace(match: re.Match) -> str:
        quote = match.group(1)
        url = match.group("url")
        tracked = build_click_url(request, recipient_id, url)
        return f'href={quote}{tracked}{quote}'

    rewritten = HREF_RE.sub(_replace, html)

    if unsubscribe_text:
        unsub = build_unsubscribe_url(request, recipient_id)
        footer = f'<p style="font-size:12px;color:#6b7280;">' \
                 f'<a href="{unsub}" target="_blank" rel="noopener">[{unsubscribe_text}]</a></p>'
        # naive append before closing body
        if "</body>" in rewritten.lower():
            # case-insensitive replace last occurrence would be nicer; keep simple:
            parts = re.split("(?i)</body>", rewritten)
            rewritten = f"{'</body>'.join(parts[:-1])}{footer}</body>{parts[-1]}"
        else:
            rewritten += footer

    return rewritten