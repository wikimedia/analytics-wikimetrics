import json
import os
import os.path
import collections

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta, date
from flask import Response


# Format string for datetime.strptime for MediaWiki timestamps.
# See <https://www.mediawiki.org/wiki/Manual:Timestamp>.
MEDIAWIKI_TIMESTAMP = '%Y%m%d%H%M%S'
# This format is used in the UI and output
PRETTY_TIMESTAMP = '%Y-%m-%d %H:%M:%S'
# This is used to mean that a result was censored in some way
CENSORED = 'censored'
# Used to mean a metric is not returning any results
NO_RESULTS = 'no-results'
# Unicode NULL
UNICODE_NULL = u'\x00'

PUBLIC_REPORT_FILE = '%Y-%m-%d'


def parse_date(date_string):
    return datetime.strptime(date_string, MEDIAWIKI_TIMESTAMP)


def format_date(date_object):
    return date_object.strftime(MEDIAWIKI_TIMESTAMP)


def format_date_for_public_report_file(date_object):
    return date_object.strftime(PUBLIC_REPORT_FILE)


def parse_pretty_date(date_string):
    return datetime.strptime(date_string, PRETTY_TIMESTAMP)


def format_pretty_date(date_object):
    return date_object.strftime(PRETTY_TIMESTAMP)


def json_string(obj):
    return json.dumps(obj, cls=BetterEncoder, indent=4)


def stringify(*args, **kwargs):
    return json_string(dict(*args, **kwargs))


def json_response(*args, **kwargs):
    """
    Handles returning generic arguments as json in a Flask application.
    Takes care of the following custom encoding duties:
        * datetime.datetime objects encoded via BetterEncoder
        * datetime.date objects encoded via BetterEncoder
        * Decimal objects encoded via BetterEncoder
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
        print(json.dumps(obj, cls=BetterEncoder))
    """
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return format_pretty_date(obj)
        
        if isinstance(obj, date):
            return format_pretty_date(obj)
        
        if isinstance(obj, Decimal):
            return float(obj)
        
        return json.JSONEncoder.default(self, obj)


def today():
    """
    Callable that gets the date today, needed by WTForms DateFields
    """
    return date.today()


def thirty_days_ago():
    """
    Callable that gets the date 30 days ago, needed by WTForms DateFields
    """
    return date.today() - timedelta(days=30)


def deduplicate(sequence):
    seen = set()
    seen_add = seen.add
    return [x for x in sequence if x not in seen and not seen_add(x)]


def deduplicate_by_key(list_of_objects, key_function):
    uniques = dict()
    for o in list_of_objects:
        key = key_function(o)
        if key not in uniques:
            uniques[key] = o
    
    return uniques.values()


def to_safe_json(s):
    return json.dumps(s).replace("'", "\\'").replace('"', '\\"')


def project_name_for_link(project):
    if project.endswith('wiki'):
        return project[:len(project) - 4]
    return project


def link_to_user_page(username, project):
    project = project_name_for_link(project)
    user_link = 'https://{0}.wikipedia.org/wiki/User:{1}'
    user_not_found_link = 'https://{0}.wikipedia.org/wiki/Username_could_not_be_parsed'
    # TODO: python 2 has insane unicode handling, switch to python 3
    try:
        return user_link.format(project, username)
    except UnicodeEncodeError:
        try:
            return user_link.format(project, username.decode('utf8'))
        except:
            return user_not_found_link.format(project)


def r(num, places=4):
    """Rounds and returns a Decimal"""
    precision = '1.{0}'.format('0' * places)
    return Decimal(num or 0).quantize(Decimal(precision), rounding=ROUND_HALF_UP)


def diff_datewise(left, right, left_parse=None, right_parse=None):
    """
    Parameters
        left        : a list of datetime strings or objects
        right       : a list of datetime strings or objects
        left_parse  : if left contains datetimes, None; else a strptime format
        right_parse : if right contains datetimes, None; else a strptime format

    Returns
        A tuple of two sets:
        [0] : the datetime objects in left but not right
        [1] : the datetime objects in right but not left
    """
    
    if left_parse:
        left_set = set([
            datetime.strptime(l.strip(), left_parse)
            for l in left if len(l.strip())
        ])
    else:
        left_set = set(left)
    
    if right_parse:
        right_set = set([
            datetime.strptime(r.strip(), right_parse)
            for r in right if len(r.strip())
        ])
    else:
        right_set = set(right)
    
    return (left_set - right_set, right_set - left_set)


def timestamps_to_now(start, increment):
    """
    Generates timestamps from @start to datetime.now(), by @increment
    
    Parameters
        start       : the first generated timestamp
        increment   : the timedelta between the generated timestamps
    
    Returns
        A generator that goes from @start to datetime.now() - x,
        where x <= @increment
    """
    now = datetime.now()
    while start < now:
        yield start
        start += increment


def strip_time(to_strip):
    """
    Strips the hours, minutes, and seconds from a datetime instance
    """
    return to_datetime(to_strip.date())


def to_datetime(d):
    """
    Converts a date to a datetime
    """
    return datetime.combine(d, datetime.min.time())


def parse_username(username):
    """
    parses uncapitalized, whitespace-padded, and weird-charactered mediawiki
    user names into ones that have a chance of being found in the database
    
    needs to accept either a unicode or string input, returns str of bytes
    """
    # not pretty but python 2.7 is a box of
    # suprises when it comes to str versus unicode types
    if not isinstance(username, unicode):
        username = username.decode('utf8', errors='ignore')
        
    parsed = username.strip()
    if len(parsed) != 0:
        parsed = parsed[0].upper() + parsed[1:]

    return parsed.encode('utf8')


def parse_tag(tag):
    parsed_tag = " ".join(tag.lower().split()).replace(" ", "-")
    return parsed_tag


def chunk(array, chunk_size):
    """
    Chunk a list into sub-lists

    Parameters
        array       : a list
        chunk_size  : max size for each returned sublist

    Returns
        array chunked up into chunk_size pieces and returned as
        a generator of those pieces (last piece might be < chunk_size)
    """
    for i in xrange(0, len(array), chunk_size):
        yield array[i : i + chunk_size]
