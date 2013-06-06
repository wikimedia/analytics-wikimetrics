#!/usr/bin/python
# TODO: because python 2.* is annoying, talk to ops about python 3

import pprint
from queue import celery
from celery import group, chord
from wikimetrics.metrics import RandomMetric
from wikimetrics.models import Cohort, ConcatMetricsJob, QueryJob
from wikimetrics.database import init_db

def main():
    metric1 = RandomMetric()
    metric2 = RandomMetric()
    cohort = Cohort()
    
    q1 = QueryJob(cohort, metric1)
    q1.run.delay(q1)
    
    c1 = ConcatMetricsJob(cohort, [metric1, metric2])
    return c1.run.delay(c1)


if __name__ == '__main__':
    init_db()
    celery.start()
    main()
