#!/usr/bin/python

import pprint
import celery
from celery import Celery
from wikimetrics.metrics import RandomMetric
from wikimetrics.models import Cohort, ConcatMetricsJob

BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

def main():
    queue = Celery('wikimetrics_tasks', broker=BROKER_URL, backend=CELERY_RESULT_BACKEND)
    
    metric1 = RandomMetric()
    metric2 = RandomMetric()
    cohort = Cohort()
    aggregator = ConcatMetricsJob(cohort, [metric1, metric2])
    result = aggregator().apply_async()
    pprint.pprint(result.get())
    
if __name__ == '__main__':
    main()

