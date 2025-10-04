from celery import shared_task

@shared_task(bind=True, queue="dispatch")
def dispatch_email(self, email_id: str) -> int:
    """
    Select fresh audience contacts, apply suppressions,
    bulk-create EmailRecipient rows in chunks,
    enqueue send tasks. Return number of recipients enqueued.
    """
    # implement later
    return 0

@shared_task(bind=True, queue="send", rate_limit=None)
def send_one(self, recipient_id: str) -> str:
    """
    Render, rewrite links, send via SMTP/SES, update recipient status.
    """
    # implement later
    return "ok"
