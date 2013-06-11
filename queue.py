# TODO: move this into wikimetrics without breaking celery
from celery import Celery

# create and configure celery app
celery = Celery('wikimetrics', include=['wikimetrics'])
celery.config_from_object('config')

if __name__ == '__main__':
    # TODO: Investigate if these really have to be imported here
    # for the queue to work
    from wikimetrics.models import ConcatMetricsJob
    from wikimetrics.models import MultiProjectMetricJob
    from wikimetrics.models import MetricJob
    celery.start()
