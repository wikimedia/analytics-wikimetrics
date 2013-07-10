import json
import datetime
from time import mktime
from flask import Response


def json_response(*args, **kwargs):
    """
    Handles returning generic arguments as json in a Flask application.
    Takes care of the following custom encoding duties:
        * datetime.datetime objects encoded via DateTimeCapableEncoder
    """
    data = json.dumps(dict(*args, **kwargs), cls=DateTimeCapableEncoder)
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
