from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'JobPlatform.settings')

app = Celery('JobPlatform')

# Use Redis as broker & backend
app.config_from_object('django.conf:settings', namespace='CELERY')

# Discover tasks from all apps automatically
app.autodiscover_tasks()

if __name__ == '__main__':
    app.start()