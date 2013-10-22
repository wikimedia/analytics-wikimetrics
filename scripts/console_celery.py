#!/usr/bin/python
import celery
from wikimetrics.models import add

c = {
    "BROKER_URL": 'redis://localhost:6379/0',
    "CELERY_RESULT_BACKEND": 'redis://localhost:6379/0',
    "CELERY_TASK_RESULT_EXPIRES": 3600,
    "DEBUG": True,
    "LOG_LEVEL": 'WARNING'
}

q = celery.Celery()
q.config_from_object(c)
r = add.delay(3, 4)

while not r.ready():
    pass

print r.result
