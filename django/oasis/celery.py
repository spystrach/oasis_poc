"""Celery configuration"""

import os

from celery import Celery
from celery.signals import setup_logging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oasis.settings")

app = Celery("oasis")
app.config_from_object("django.conf:settings", namespace="CELERY")


@setup_logging.connect
def config_loggers(*args, **kwags):
    from logging.config import dictConfig
    from django.conf import settings

    dictConfig(settings.LOGGING)


app.autodiscover_tasks()
