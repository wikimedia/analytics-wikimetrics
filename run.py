#!/usr/bin/python
# TODO: because python 2.* is annoying, talk to ops about python 3

import pprint
from queue import celery
from wikimetrics.metrics import RandomMetric
from wikimetrics.models import Cohort, ConcatMetricsJob

def main():
    metric1 = RandomMetric()
    metric2 = RandomMetric()
    cohort = Cohort()
    job = ConcatMetricsJob(cohort, [metric1, metric2])
    result = job.run.delay(job)
    pprint.pprint(result.get())


if __name__ == '__main__':
    celery.start()
    main()
