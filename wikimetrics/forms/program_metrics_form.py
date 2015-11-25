import uuid

from wtforms import HiddenField
from wikimetrics.forms.fields import BetterDateTimeField
from wikimetrics.forms.validators import NotGreater
from wikimetrics.utils import thirty_days_ago, today
from cohort_upload import CohortUpload


class ProgramMetricsForm(CohortUpload):
    """
    Defines the fields necessary to upload inputs to calculate
    the ProgramMetrics
    """
    # Override cohort name and default project
    # The user for the ProgramMetrics API doesn't have to define these
    name                    = HiddenField(
        default='ProgramGlobalMetricsCohort_' + str(uuid.uuid1()))
    project                 = HiddenField(default='enwiki')
    validate_as_user_ids    = HiddenField(default='False')
    start_date              = BetterDateTimeField(
        default=thirty_days_ago, validators=[NotGreater('end_date')])
    end_date                = BetterDateTimeField(default=today)
