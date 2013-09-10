from sqlalchemy import TypeDecorator, Unicode
from datetime import datetime
from wikimetrics.utils import parse_date, format_date

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
        """
        if not value:
            return None
        return parse_date(value)
