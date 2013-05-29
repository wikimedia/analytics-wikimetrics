from celery import Celery

# create and configure celery app
celery = Celery('wikimetrics', include=['wikimetrics'])
celery.config_from_object('config')
