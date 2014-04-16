from validated_cohort import ValidatedCohort


class CentralAuthCohort(ValidatedCohort):
    """
    A cohort whose wiki users have been expanded using centralauth database
    to consider all user's accounts across different projects.
    """
