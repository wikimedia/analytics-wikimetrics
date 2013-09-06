import json
import datetime
import decimal
from time import mktime
from flask import Response


def stringify(*args, **kwargs):
    return json.dumps(dict(*args, **kwargs), cls=BetterEncoder, indent=4)


def json_response(*args, **kwargs):
    """
    Handles returning generic arguments as json in a Flask application.
    Takes care of the following custom encoding duties:
        * datetime.datetime objects encoded via BetterEncoder
        * datetime.date objects encoded via BetterEncoder
        * decimal.Decimal objects encoded via BetterEncoder
    """
    data = stringify(*args, **kwargs)
    return Response(data, mimetype='application/json')


def json_error(message):
    """
    Standard json error response for when the ajax caller would rather
    have a message with a status 200 than a server error.
    """
    return json_response(isError=True, message=message)


def json_redirect(url):
    """
    Standard json redirect response, for when a client-side redirect
    is needed.
    """
    return json_response(isRedirect=True, redirectTo=url)


class BetterEncoder(json.JSONEncoder):
    """
    Date/Time objects are not serializable by the built-in
    json library because there is no agreed upon standard of how to do so
    This class can be used as follows to allow your json.dumps to serialize
    dates properly.  You should make sure your client is happy with this serialization:
        print json.dumps(obj, cls=BetterEncoder)
    """
    
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return int(mktime(obj.timetuple()))
        
        if isinstance(obj, datetime.date):
            return int(mktime(obj.timetuple()))
        
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        
        return json.JSONEncoder.default(self, obj)


def today():
    """
    Callable that gets the date today, needed by WTForms DateFields
    """
    return datetime.date.today()


def thirty_days_ago():
    """
    Callable that gets the date 30 days ago, needed by WTForms DateFields
    """
    return datetime.date.today() - datetime.timedelta(days=30)


def deduplicate(sequence):
    seen = set()
    seen_add = seen.add
    return [x for x in sequence if x not in seen and not seen_add(x)]


def deduplicate_by_key(list_of_objects, key_function):
    uniques = dict()
    for o in list_of_objects:
        key = key_function(o)
        if not key in uniques:
            uniques[key] = o
    
    return uniques.values()
