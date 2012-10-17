
#CELERY CONFIG

SITE_ID = 1

## Broker settings
BROKER_URL = "redis://localhost:6379/0"

## Using the database to store task state and results.
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_TASK_RESULT_EXPIRES = 18000  # 5 hours.

#CELERY_REDIS_CONNECT_RETRY = True
CELERY_TIMEZONE = 'Europe/Madrid'
CELERY_ENABLE_UTC = True
