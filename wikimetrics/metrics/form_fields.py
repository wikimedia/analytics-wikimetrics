from wtforms import Field, BooleanField
from wtforms.widgets import TextInput


def better_bool(value):
    if type(value) is bool:
        return value
    elif type(value) is list and len(value) > 0:
        value = value[0]
    else:
        return False
    
    return str(value).strip().lower() in ['yes', 'y', 'true']


class BetterBooleanField(BooleanField):
    
    def process_formdata(self, valuelist):
        # Checkboxes and submit buttons simply do not send a value when
        # unchecked/not pressed. So the actual value="" doesn't matter for
        # purpose of determining .data, only whether one exists or not.
        self.data = better_bool(valuelist)


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
    
    def process_formdata(self, valuelist):
        """ overrides wtforms parsing to split list into namespaces """
        if valuelist:
            self.data = [int(x.strip()) for x in valuelist[0].split(',') if x.strip().isdigit()]
        else:
            self.data = []
