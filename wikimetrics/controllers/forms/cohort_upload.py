import csv
from wtforms import StringField, FileField, TextAreaField, RadioField
from wtforms.validators import Required
from wikimetrics.metrics.form_fields import RequiredIfNot

from secure_form import WikimetricsSecureForm


class CohortUpload(WikimetricsSecureForm):
    """
    Defines the fields necessary to upload a cohort from a csv file
    """
    name                    = StringField([Required()])
    description             = TextAreaField()
    project                 = StringField('Default Project', [Required()])
    csv                     = FileField('Upload File', [RequiredIfNot('paste_usernames')])
    paste_username          = TextAreaField('Paste Usernames', [RequiredIfNot('csv')])
    validate_as_user_ids    = RadioField('Validate As', [Required()], choices=[
        ('True', 'User Ids (Numbers found in the user_id column of the user table)'),
        ('False', 'User Names (Names found in the user_name column of the user table)')
    ])
    
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
        You must call this to parse self.records out of the csv file
        
        Parameters
            request : the request with the file to parse
        
        Returns
            nothing, but sets self.records to the parsed lines of the csv
        """

        if self.csv.data:
            csv_file = normalize_newlines(self.csv.data.stream)
            unparsed = csv.reader(csv_file)

        else:
            #TODO: Check valid input
            unparsed = parse_textarea_usernames(self.paste_username.data)

        self.records = parse_records(unparsed, self.project.data)


def parse_records(unparsed, default_project):
    """
    Parses records read from a csv file
    
    Parameters
        unparsed        : records in array form, as read from a csv
        default_project : the default project to attribute to records without one
    
    Returns
        the parsed records in this form:
            {'username':'parsed username', 'project':'as specified or default'}
    """
    records = []
    for r in unparsed:
        if r is not None and len(r) > 0:
            # NOTE: the reason for the crazy -1 and comma joins
            # is that some users can have commas in their name
            # NOTE: This makes it impossible to add fields to the csv in the future,
            # so maybe require the project to be the first field
            # and the username to be the last or maybe change to a tsv format
            if len(r) > 1:
                username = ",".join([str(p) for p in r[:-1]])
                project = r[-1].decode('utf8') or default_project
            else:
                username = r[0]
                project = default_project
            
            if username is not None and len(username):
                records.append({
                    'username'  : parse_username(username),
                    'project'   : project,
                })
    return records


def parse_username(username):
    """
    parses uncapitalized, whitespace-padded, and weird-charactered mediawiki
    user names into ones that have a chance of being found in the database
    """
    assert(type(username) != unicode)
    username = str(username)
    username = username.decode('utf8', errors='ignore')
    parsed = username.strip()
    if len(parsed) != 0:
        parsed = parsed[0].upper() + parsed[1:]
    
    return parsed.encode('utf8')


def normalize_newlines(lines):
    for line in lines:
        if '\r' in line:
            for tok in line.split('\r'):
                yield tok
        else:
            yield line


def parse_textarea_usernames(paste_username):
    """
    Takes csv format text and parses it into a list of lists of usernames
    and their wiki. i.e. "dan,en v" becomes [['dan','en'],['v']]. Whitespace is
    the delimiter of each list. Prepares text to go through parse_records().
    """
    for username in paste_username.split():
        yield username.strip().split(',')
