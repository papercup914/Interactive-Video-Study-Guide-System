import os
import ssl
import certifi
from celery import Celery
from dotenv import load_dotenv

load_dotenv(override=True)

redis_url = os.getenv("REDIS_URL", "").strip()
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "").strip() or redis_url or "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "").strip() or redis_url or "redis://localhost:6379/0"

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
