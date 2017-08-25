import csv
from flask import g
from wikimetrics.configurables import db
from wtforms import StringField, FileField, TextAreaField, RadioField
from wikimetrics.forms.fields import BetterBooleanField
from wtforms.validators import Required

from wikimetrics.utils import parse_username
from secure_form import WikimetricsSecureForm
from validators import (
    CohortNameUnused, CohortNameLegalCharacters, ProjectExists, RequiredIfNot
)


class CohortUpload(WikimetricsSecureForm):
    """
    Defines the fields necessary to upload a cohort from a csv file or
    a textbox.
    """
    name                    = StringField('Name',
                                          [Required(), CohortNameUnused(),
                                           CohortNameLegalCharacters()])

    description             = TextAreaField()
    project                 = StringField('Default Project',
                                          [Required(), ProjectExists()])

    csv                     = FileField('Upload File',
                                        [RequiredIfNot('paste_ids_or_names')])
    paste_ids_or_names      = TextAreaField('Paste User Names or IDs',
                                            [RequiredIfNot('csv')])
    validate_as_user_ids    = RadioField('Validate As', [Required()], choices=[
        ('True', 'User Ids (Numbers found in the user_id column of the user table)'),
        ('False', 'User Names (Names found in the user_name column of the user table)')
    ])
    centralauth             = BetterBooleanField(default=True)

    @classmethod
    def from_request(cls, request):
        """
        Calls the constructor with the union of request.form and request.files
        """
        values = request.form.copy()
        values.update(request.files)
        return cls(values)

    def parse_records(self):
        """
        Called by controller code to parse form submission, it being a cvs file
        or input box

        Returns
            nothing, but sets self.records to the parsed lines of the csv
            as string types
        """

        if self.csv.data:
            # uploaded a cohort file
            csv_lines = normalize_newlines(self.csv.data.stream)

        else:
            # used upload box, note that wtforms returns unicode types here
            csv_lines = parse_textarea_ids_or_names(self.paste_ids_or_names.data)

        records = format_records(csv_lines, self.project.data)

        if self.centralauth.data is True:
            ca_session = db.get_ca_session()
            records = g.centralauth_service.expand_via_centralauth(records, ca_session)

        self.records = records


def format_records(csv_lines, default_project):
    """
    Processes and formats lines read from a csv file or coming from the upload box.
    i.e. "dan,en" becomes {'raw_id_or_name': 'dan', 'project': 'en'}, and
    "1, en" becomes {'raw_id_or_name': '1', 'project': 'en'}.
    Note this method assumes bytes (str) not unicode types as input

    Parameters
        csv_lines       : collection of strings, each with csv format
        default_project : the default project to attribute to records without one

    Returns
        a list of the formatted records in which each element is of this form:
        {'raw_id_or_name':'parsed user name or id', 'project':'as specified or default'}
    """
    records = []
    for r in csv.reader(csv_lines):
        if r is not None and len(r) > 0:
            # NOTE: the reason for the crazy -1 and comma joins
            # is that some users can have commas in their name
            # NOTE: This makes it impossible to add fields to the csv in the future,
            # so maybe require the project to be the first field
            # and the username to be the last or maybe change to a tsv format
            if len(r) > 1:
                raw_id_or_name = ",".join([str(p) for p in r[:-1]])
                project = r[-1].strip() or default_project
            else:
                raw_id_or_name = r[0]
                project = default_project

            if raw_id_or_name is not None and len(raw_id_or_name):
                records.append({
                    'raw_id_or_name'  : parse_username(raw_id_or_name),
                    'project'         : project,
                })
    return records


def normalize_newlines(lines):
    for line in lines:
        if '\r' in line:
            for tok in line.split('\r'):
                tok = tok.strip()
                if tok != '':
                    yield tok
        else:
            yield line


def parse_textarea_ids_or_names(textarea_contents):
    """
    Prepares text to go through format_records().

    Note that textarea_contents is going to be a unicode type as flask builds it
    that way. Output is plain bytes (str type) as the rest of our code
    does not assume unicode types.

    Parameters
        textarea_contents : the text pasted into the textarea.

    Returns
        list of strings, each holding a line of the input.
        Unicode types are transformed to bytes.
    """
    return textarea_contents.encode('utf-8').splitlines()
