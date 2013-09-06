from sqlalchemy import TypeDecorator, Unicode
from datetime import datetime

__all__ = ['MediawikiTimestamp']


# Format string for datetime.strptime for MediaWiki timestamps.
# See <http://www.mediawiki.org/wiki/Manual:Timestamp>.
MEDIAWIKI_TIMESTAMP = '%Y%m%d%H%M%S'


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
            value = value.strftime(MEDIAWIKI_TIMESTAMP)
        #if hasattr(value, 'decode'):
            #value = value.decode('utf-8')
        return unicode(value)
    
    def process_result_value(self, value, dialect=None):
        """
        Convert a MediaWiki timestamp to a datetime object.
        """
        if not value:
            return None
        return datetime.strptime(value, MEDIAWIKI_TIMESTAMP)
