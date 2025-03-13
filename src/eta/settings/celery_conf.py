# Celery settings
CELERY_ENABLED = True

CELERY_BROKER_URL = "amqp://user1:rabbitmq@rabbit//"
CELERY_RESULT_BACKEND = "redis://redis:6379"
CELERY_CACHE_BACKEND = "redis://redis:6379"
CELERY_ACCEPT_CONTENT = {"application/json"}
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"

# BEAT SETTINGS
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
