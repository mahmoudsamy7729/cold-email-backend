import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("coldreach")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()  # finds tasks.py in installed apps

# Optional: explicit queues
from kombu import Queue, Exchange
app.conf.task_queues = (
    Queue("dispatch", Exchange("dispatch"), routing_key="dispatch"),
    Queue("send", Exchange("send"), routing_key="send"),
)
