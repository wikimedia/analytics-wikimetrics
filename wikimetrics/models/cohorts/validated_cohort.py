from cohort import Cohort, CohortProperty


class ValidatedCohort(Cohort):
    """
    A cohort that's been validated by wikimetrics
    """
    validated               = CohortProperty()
    validate_as_user_ids    = CohortProperty()
    validation_queue_key    = CohortProperty()
