import celery
from report import ReportLeaf
from celery import current_task

from wikimetrics.utils import stringify
from wikimetrics.configurables import db


class ValidateReport(ReportLeaf):
    """
    Checks if a metric and cohort are valid.  If they're not, this ReportLeaf
    can be added to a Report hierarchy and will report the appropriate errors
    """
    
    show_in_ui = False
    
    def __init__(self, metric, cohort, validate_csrf, *args, **kwargs):
        """
        Parameters
            metric          : an instance of a wikimetrics.metrics.metric.Metric
            cohort          : an instance of a wikimetrics.models.cohort.Cohort
            validate_csrf   : whether the metric should validate its CSRF
        """
        super(ValidateReport, self).__init__(*args, **kwargs)
        if validate_csrf is False:
            metric.disable_csrf()
        self.metric_valid = metric.validate()
        self.cohort_valid = cohort.validated
        self.metric_label = metric.label
        self.cohort_name = cohort.name
    
    def valid(self):
        return self.metric_valid and self.cohort_valid
    
    def run(self):
        """
        This will get executed if the instance is added into a Report node hierarchy
        It outputs failure messages due to any invalid configuration.  None of these
        failures should happen unless the user tries to hack the system.
        """
        self.set_status(celery.states.STARTED, task_id=current_task.request.id)
        session = db.get_session()
        try:
            from wikimetrics.models import PersistentReport
            pj = session.query(PersistentReport).get(self.persistent_id)
            pj.name = '{0} - {1} (failed validation)'.format(
                self.metric_label,
                self.cohort_name,
            )
            pj.status = celery.states.FAILURE
            session.commit()
        finally:
            session.close()
        
        message = ''
        if not self.cohort_valid:
            message += '{0} ran with invalid cohort {1}\n'.format(
                self.metric_label,
                self.cohort_name,
            )
        if not self.metric_valid:
            message += '{0} was incorrectly configured\n'.format(
                self.metric_label,
            )
        return {'FAILURE': message or 'False'}
    
    def __repr__(self):
        return '<ValidateReport("{0}")>'.format(self.persistent_id)
