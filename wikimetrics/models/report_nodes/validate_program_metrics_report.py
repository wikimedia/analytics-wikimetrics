import celery
from report import ReportLeaf
from celery import current_task
from wikimetrics.api import CohortService


class ValidateProgramMetricsReport(ReportLeaf):
    """
    Checks if the cohort is valid (it should be validated, and >=50% of the
    cohort members must be valid.  If not, this ReportLeaf
    can be added to a Report hierarchy and will report the appropriate errors
    """
    
    show_in_ui = False
    
    def __init__(self, cohort, session, *args, **kwargs):
        """
        Parameters
            cohort          : an instance of CohortStore
            session         : DB session instance
        """
        super(ValidateProgramMetricsReport, self).__init__(*args, **kwargs)
        self.cohort = cohort
        self.session = session
        self.validation_info = self.get_validation_info()
        self.unique_users = self.validation_info['unique_users']
        self.cohort_valid = self.is_cohort_valid()

    def get_validation_info(self):
        cohort_service = CohortService()
        return cohort_service.get_validation_info(self.cohort,
                                                  self.session,
                                                  True)

    def is_cohort_valid(self):
        if self.validation_info['percentage_valid'] >= 50.0:
            return True
        else:
            return False

    def valid(self):
        return self.cohort_valid

    def run(self):
        """
        This will get executed if the instance is added into a Report node hierarchy
        It outputs failure messages due to any invalid configuration.  None of these
        failures should happen unless the user tries to hack the system.
        """
        self.set_status(celery.states.STARTED, task_id=current_task.request.id)
        
        message = ''
        if not self.cohort_valid:
            message += 'Cohort invalid: >=50% of the cohort members are not valid'
        return {'FAILURE': message or 'False'}
