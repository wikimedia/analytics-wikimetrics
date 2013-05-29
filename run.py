#!/usr/bin/python
# TODO: because python 2.* is annoying, talk to ops about python 3

import pprint
from queue import celery
from celery import group, chord
from wikimetrics.metrics import RandomMetric
from wikimetrics.models import Cohort, ConcatMetricsJob, QueryJob

def main():
    metric1 = RandomMetric()
    metric2 = RandomMetric()
    cohort = Cohort()
    
    # NOTE: these next five lines work, yay!
    #q1 = QueryJob(cohort, metric1)
    #q2 = QueryJob(cohort, metric2)
    #g = group(q1.run.s(q1), q2.run.s(q2))
    #c = chord(g)(c1.finish.s())
    #print c.get()
    
    c1 = ConcatMetricsJob(cohort, [metric1, metric2])
    c1.run.delay(c1)


if __name__ == '__main__':
    celery.start()
    main()
