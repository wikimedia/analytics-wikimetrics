import json
import datetime
from time import mktime

class DateTimeCapableEncoder(json.JSONEncoder):
    """
    Date/Time objects are not serializable by the built-in
    json library because there is no agreed upon standard of how to do so
    This class can be used as follows to allow your json.dumps to serialize dates properly.
    You should make sure your client is happy with this serialization:
        print json.dumps(obj, cls=DateTimeCapableEncoder)
    """
    
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return int(mktime(obj.timetuple()))

        return json.JSONEncoder.default(self, obj)

