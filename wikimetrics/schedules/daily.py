from celery.utils.log import get_task_logger
from wikimetrics.configurables import queue


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
                days_to_run = RunReport.create_reports_for_missed_days(report, session)
                for day_to_run in days_to_run:
                    day_to_run.task.delay(day_to_run)
            except Exception, e:
                task_logger.error('Problem running recurring report "{0}": {1}'.format(
                    report, e
                ))
    except Exception, e:
        task_logger.error('Problem running recurring reports: {0}'.format(e))
    finally:
        session.close()
