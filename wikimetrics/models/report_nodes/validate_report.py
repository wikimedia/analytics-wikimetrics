from report import ReportLeaf
from wikimetrics.utils import stringify


class ValidateReport(ReportLeaf):
    """
    Checks if a metric and cohort are valid.  If they're not, this ReportLeaf
    can be added to a Report hierarchy and will report the appropriate errors
    """
    
    show_in_ui = True
    
    def __init__(self, metric, cohort):
        """
        Parameters
            metric  : an instance of a wikimetrics.metrics.metric.Metric
            cohort  : an instance of a wikimetrics.models.cohort.Cohort
        """
        super(ValidateReport, self).__init__(parameters=stringify(metric.data))
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
