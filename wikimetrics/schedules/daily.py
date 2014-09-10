import traceback
from celery import group, chain
from celery.utils.log import get_task_logger

from wikimetrics.api import ReplicationLagService
from wikimetrics.configurables import queue
from wikimetrics.utils import chunk


task_logger = get_task_logger(__name__)


# NOTE: We found an interesting problem leading to the default timeouts expiring.
#       The scheduler would run, create the generator of child reports, and delay each one
#       This works but causes the scheduler to execute more slowly (we think because the
#       workers handling the report tasks are taking up resources).  So in a situation
#       where reports are running quickly, this task will need to be allowed to live
#       for the entire life of all the other tasks.  Therefore, extending timeout to 3
#       times the amount allotted to normal tasks.
configured_soft_limit = queue.conf.get('CELERYD_TASK_SOFT_TIME_LIMIT', 3600)
new_limit = 3 * configured_soft_limit


@queue.task(time_limit=new_limit, soft_time_limit=new_limit)
def recurring_reports(report_id=None):
    from wikimetrics.configurables import db
    from wikimetrics.models import ReportStore, RunReport
    
    replication_lag_service = ReplicationLagService()
    if replication_lag_service.is_any_lagged():
        task_logger.warning(
            'Replication lag detected. '
            'Hence, skipping creating new recurring reports.'
        )
        return

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


if queue.conf.get('DEBUG'):
    @queue.task
    def get_session_and_leave_open(*args, **kwargs):
        from wikimetrics.configurables import db
        from wikimetrics.models import ReportStore, RunReport
        session = db.get_session()
        session2 = db.get_session()
        session2.query(ReportStore).first()
        session.query(ReportStore).first()
