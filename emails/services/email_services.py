from dataclasses import dataclass

@dataclass
class RenderedEmail:
    subject: str
    html: str | None
    text: str | None

def render_template(template_id: str, context: dict) -> str:
    """
    Replace with your renderer later.
    Assumption: template supports a single slot {{ body }}.
    """
    # Pseudocode example:
    # template_html = TemplatesRepo.get_html(template_id)
    # return template_engine.render(template_html, context)
    raise NotImplementedError

def build_send_payload(email: "Email") -> RenderedEmail:
    if email.uses_template:
        html = render_template(str(email.template_id), {"body": email.content_text})
        return RenderedEmail(subject=email.subject, html=html, text=None)
    else:
        # No template -> send plain text as-is
        return RenderedEmail(subject=email.subject, html=None, text=email.content_text)
