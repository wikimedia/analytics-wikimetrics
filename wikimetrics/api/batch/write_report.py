import os
import celery
from celery.exceptions import SoftTimeLimitExceeded
from celery.utils.log import get_task_logger
from celery import current_task
# TODO split configurables, you should be able to import just the queue
from wikimetrics.configurables import queue, get_absolute_path
from wikimetrics.api import PublicReportFileManager, COALESCED_REPORT_FILE
from wikimetrics.utils import format_date_for_public_report_file, json_string

# This is the hack you need if you use instance methods as celery tasks
# from celery.contrib.methods import task_methods
__all__ = [
    'write_report_task',
    'WriteReportTask',
    'COALESCED_REPORT_FILE'
]

task_logger = get_task_logger(__name__)


@queue.task()
def write_report_task(report_id, created, results):
    
    task_logger.info('Writing report {0} to disk.Running on celery as task id {1}'.format(
        report_id,
        current_task.request.id,
    ))
    
    write_task = WriteReportTask(report_id, created, results)
    write_task.run()


class WriteReportTask(object):
    """
    Task in charge of dumping a report that was executed sucessfully to disk
    via file_manager.
    
    """
    
    def __init__(self, report_id, created, results, file_manager=None):
        """
        TODO: Add dependency injection for the file_manager,
        we are passing it on the constructor for easier testing
        but the object should come from the application context
        
        Parameters:
            report_id   : identifier of the report, needed to find
                          directory to write to if report is recurrent
            created     : date report was created, used to identify a single run of
                          a recurrent report
            results     : data to write to disk
            file_manager: PublicReportFileManager, adding to constructor
                          for easy testing.
        """
        
        self.report_id = report_id
        self.created_string = format_date_for_public_report_file(created)
        self.results = json_string(results)
        
        self.file_manager = file_manager or PublicReportFileManager(task_logger,
                                                                    get_absolute_path())
                  
        # there should not be a need to call these functions more than once
        self.path = self.file_manager.get_public_report_path(self.report_id,
                                                             recurrent=True,
                                                             create=True)
        
        # TODO use file manager to get function when function is available
        self.filepath = os.path.join(self.path, self.created_string)
        
    def run(self):
        try:
            # TODO kind of cumbersome api on file_manager, look into simplifying
            self.file_manager.write_data(self.filepath, self.results)
            self.create_coalesced_report()
            self.file_manager.remove_old_report_files(self.report_id)
        except SoftTimeLimitExceeded:
            task_logger.error('timeout exceeded for {0}'.format(
                current_task.request.id
            ))
            raise
    
    def create_coalesced_report(self):
        """
        Creates coalesced report.
        
        for CR: should we create the report everytime or make sure to create it
        only if coalesced report on disk is more than one day old?.
        """
        data = self.file_manager.coalesce_recurrent_reports(self.report_id)
        
        if data is not None:
            coalesced_report_file_path = os.path.join(self.path, COALESCED_REPORT_FILE)
            self.file_manager.write_data(coalesced_report_file_path, json_string(data))
