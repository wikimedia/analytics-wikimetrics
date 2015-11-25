from batch import write_report_task
from wikimetrics.models.storage.report import ReportStore


class ReportService(object):

    def write_report_to_file(self, report, results, db_session):
        """
        Helper to write results of a report to file.

        The post_process method in RunReport and RunProgramMetricsReport have
        the uses this functionality to write public reports, so we abstract it here.
        """
        db_report = db_session.query(ReportStore).get(report.persistent_id)

        data = db_report.get_json_result(results)

        # code below schedules an async task on celery to write the file
        report_id_to_write = report.persistent_id
        if report.recurrent_parent_id is not None:
            report_id_to_write = report.recurrent_parent_id
        write_report_task.delay(report_id_to_write, report.created, data)
