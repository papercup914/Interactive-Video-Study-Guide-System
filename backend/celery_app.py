import os
import ssl
import certifi
from celery import Celery
from backend.config import settings

CELERY_BROKER_URL = settings.get_celery_broker()
CELERY_RESULT_BACKEND = settings.get_celery_backend()

celery_app = Celery(
    "studyguide_worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["backend.services.tasks"]
)

conf_update = {
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "Asia/Seoul",
    "enable_utc": True,
    "broker_connection_retry_on_startup": True,
    "worker_max_tasks_per_child": 10
}

# Apply strict SSL verification for rediss:// connections using certifi CA bundle
if CELERY_BROKER_URL.startswith("rediss://"):
    ssl_options = {
        "ssl_cert_reqs": ssl.CERT_REQUIRED,
        "ssl_ca_certs": certifi.where()
    }
    conf_update["broker_use_ssl"] = ssl_options
    conf_update["redis_backend_use_ssl"] = ssl_options

celery_app.conf.update(**conf_update)
