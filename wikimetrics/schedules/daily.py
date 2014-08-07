import sys
import traceback
from celery import group, chain
from celery.utils.log import get_task_logger

from wikimetrics.configurables import queue
from wikimetrics.utils import chunk


task_logger = get_task_logger(__name__)


@queue.task()
def recurring_reports(report_id=None):
    from wikimetrics.configurables import db
    from wikimetrics.models import ReportStore, RunReport
    
    try:
        session = db.get_session()
        query = session.query(ReportStore) \
            .filter(ReportStore.recurrent) \
        
        if report_id is not None:
            query = query.filter(ReportStore.id == report_id)
        
        for report in query.all():
            try:
                task_logger.info('Running recurring report "{0}"'.format(report))
                no_more_than = queue.conf.get('MAX_INSTANCES_PER_RECURRENT_REPORT')
                kwargs = dict()
                if no_more_than:
                    kwargs['no_more_than'] = no_more_than

                days_to_run = RunReport.create_reports_for_missed_days(
                    report,
                    session,
                    **kwargs
                )
                for day_to_run in days_to_run:
                    day_to_run.task.delay(day_to_run)

            except Exception:
                task_logger.error('Problem running recurring report "{}": {}'.format(
                    report, traceback.format_exc()
                ))
    
    except Exception:
        task_logger.error('Problem running recurring reports: {}'.format(
            traceback.format_exc()
        ))
    finally:
        session.close()
