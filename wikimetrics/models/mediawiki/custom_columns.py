from sqlalchemy import TypeDecorator, Unicode, Interval
from datetime import datetime
from wikimetrics.utils import parse_date, format_date, UNICODE_NULL

__all__ = ['MediawikiTimestamp']


class MediawikiTimestamp(TypeDecorator):
    """
    A TypeDecorator for MediaWiki timestamps
    which are stored as VARBINARY(14) columns.
    """
    
    impl = Unicode(14)
    
    def process_bind_param(self, value, dialect=None):
        """
        Convert an integer timestamp (specifying number of seconds or
        miliseconds since UNIX epoch) to MediaWiki timestamp format.
        """
        if not value:
            return None
        if isinstance(value, datetime):
            value = format_date(value)
        #if hasattr(value, 'decode'):
            #value = value.decode('utf-8')
        return unicode(value)
    
    def process_result_value(self, value, dialect=None):
        """
        Convert a MediaWiki timestamp to a datetime object.
        To unbundle we have to detect unicodestrings that are set as mysql defaults
        they are not represented by singleton None
        """
        if not value or value == UNICODE_NULL * 14:
            return None
        return parse_date(value)
