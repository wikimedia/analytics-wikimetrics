#!/usr/bin/python
# TODO: because python 2.* is annoying, talk to ops about python 3

import pprint
import celery
from celery import Celery
from wikimetrics.metrics import RandomMetric
from wikimetrics.models import Cohort, ConcatMetricsJob

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_DISABLE_RATE_LIMITS = True

def main():
    queue = Celery(
        'wikimetrics_tasks',
        broker=CELERY_BROKER_URL,
        backend=CELERY_RESULT_BACKEND
    )
    
    metric1 = RandomMetric()
    metric2 = RandomMetric()
    cohort = Cohort()
    job = ConcatMetricsJob(cohort, [metric1, metric2])
    result = job.run.apply_async()
    pprint.pprint(result.get())



if __name__ == '__main__':
    main()
