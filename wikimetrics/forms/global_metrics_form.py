import uuid

from flask import g
from wikimetrics.configurables import db
from wtforms import HiddenField
from wikimetrics.forms.fields import BetterBooleanField, BetterDateTimeField
from wtforms.validators import Required
from wikimetrics.forms.validators import NotGreater
from wikimetrics.utils import parse_username, thirty_days_ago, today, format_pretty_date
from cohort_upload import CohortUpload
from validators import (
    CohortNameUnused, CohortNameLegalCharacters, ProjectExists, RequiredIfNot
)


class GlobalMetricsForm(CohortUpload):
    """
    Defines the fields necessary to upload inputs to calculate
    the global metrics
    """
    # Override cohort name and default project
    # The user for the Global API doesn't have to define these
    name                    = HiddenField(default='GlobalCohort_' + str(uuid.uuid1()))
    project                 = HiddenField(default='enwiki')
    validate_as_user_ids    = HiddenField(default='False')
    start_date              = BetterDateTimeField(
        default=thirty_days_ago, validators=[NotGreater('end_date')])
    end_date                = BetterDateTimeField(default=today)
