from celery.utils.log import get_task_logger
from wikimetrics.configurables import queue


task_logger = get_task_logger(__name__)


@queue.task()
def recurring_reports():
    pass
