import re
from wtforms import ValidationError
from wtforms.validators import Required

from wikimetrics.configurables import db
from wikimetrics.api import CohortService


class CohortNameUnused(object):
    """
    Checks that a cohort name is unused.

    Note: the same message appears in static/js/cohortUpload.js, and the same
    logic is in wikimetrics.controllers.cohorts.validate_cohort_name_allowed().
    This is because the upload form is validated on both the client and the server.

    TODO: Maybe add this constraint to the model, too?
    """

    def __call__(self, form, field):
        session = db.get_session()

        if CohortService().get_cohort_by_name(session, field.data) is not None:
            raise ValidationError('This cohort name is taken.')


class CohortNameLegalCharacters(object):
    """
    Checks that a cohort name only contains allowed characters.
    Note: the same logic and message also appear in static/js/cohortUpload.js.
    This is because the upload form is validated on both the client and the server.
    """

    def __call__(self, form, field):

        if not re.match(r"^[0-9_\-A-Za-z ]*$", field.data):
            raise ValidationError('Cohort names should only contain letters, '
                                  'numbers, spaces, dashes, and underscores.')


class ProjectExists(object):
    """
    Checks that a project exists.
    Note: the same message appears in static/js/cohortUpload.js, and the same
    logic is in wikimetrics.controllers.cohorts.validate_cohort_project_allowed().
    This is because the upload form is validated on both the client and the server.
    """

    def __call__(self, form, field):

        if field.data not in db.get_project_host_map():
            raise ValidationError('That project does not exist.')


class RequiredIfNot(Required):
    """
    A validator which makes a field mutually exclusive with another
    """

    def __init__(self, other_field_name, *args, **kwargs):
        self.other_field_name = other_field_name
        super(RequiredIfNot, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = form._fields.get(self.other_field_name)
        other_field_set = other_field and bool(other_field.data)
        field_set = field and bool(field.data)
        if other_field_set == field_set:
            raise ValidationError('Please use either {0} or {1}'.format(
                other_field.label.text, field.label.text
            ))
