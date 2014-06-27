from cohort import Cohort, CohortProperty


class ValidatedCohort(Cohort):
    """
    A cohort that needs to be validated to be used
    """
    has_validation_info     = True
    validated               = CohortProperty()
    validate_as_user_ids    = CohortProperty()
    validation_queue_key    = CohortProperty()
