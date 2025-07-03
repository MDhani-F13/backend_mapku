from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Pastikan pakai settings Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_mapku.settings')

app = Celery('backend_mapku')

# Load config dari settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto discovery tasks.py di setiap module
app.autodiscover_tasks()
