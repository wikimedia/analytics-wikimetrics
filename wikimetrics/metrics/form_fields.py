from datetime import datetime, date, time
from wtforms import Field, BooleanField, DateField, DateTimeField
from wtforms.validators import Required, ValidationError
from wtforms.widgets import TextInput


class BetterBooleanField(BooleanField):
    
    def process_formdata(self, valuelist):
        # Checkboxes and submit buttons simply do not send a value when
        # unchecked/not pressed. So the actual value="" doesn't matter for
        # purpose of determining .data, only whether one exists or not.
        self.data = BetterBooleanField.better_bool(valuelist)
    
    @staticmethod
    def better_bool(value):
        if type(value) is bool:
            return value
        elif type(value) is list and len(value) > 0:
            value = value[0]
        else:
            return False
        
        return str(value).strip().lower() in ['yes', 'y', 'true']


class CommaSeparatedIntegerListField(Field):
    
    def __iter__(self):
        return iter(self.data)
    
    widget = TextInput()
    
    def _value(self):
        """ overrides the representation wtforms sends to the server """
        if self.data and len(self.data) > 0:
            return u', '.join(map(unicode, self.data))
        else:
            return u''
    
    def process_data(self, value):
        if isinstance(value, list):
            self.data = value
        else:
            if value:
                self.process_formdata([value])
            else:
                self.data = []
    
    def process_formdata(self, valuelist):
        """ overrides wtforms parsing to split list into namespaces """
        if valuelist:
            self.data = [
                int(x.strip())
                for x in valuelist[0].split(',')
                if x.strip().isdigit()
            ]
        else:
            self.data = []


class BetterDateTimeField(DateTimeField):
    
    def parse_datetime(self, value):
        if not value:
            self.report_invalid()
        
        if isinstance(value, date):
            value = datetime.combine(value, time())
        
        if isinstance(value, datetime):
            return value
        
        try:
            return datetime.strptime(value, self.format)
        except ValueError:
            self.report_invalid()

    def process_data(self, value):
        self.data = self.parse_datetime(value)
    
    def process_formdata(self, valuelist):
        if not valuelist:
            self.report_invalid()
        
        self.data = self.parse_datetime(' '.join(valuelist))
    
    def report_invalid(self):
        self.data = None
        raise ValueError(self.gettext('Not a valid datetime value'))


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
