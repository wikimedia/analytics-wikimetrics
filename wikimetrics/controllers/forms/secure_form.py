from flask import session
from flask import current_app
from datetime import timedelta

from wikimetrics.configurables import app
from wtforms.ext.csrf.session import SessionSecureForm


class WikimetricsSecureForm(SessionSecureForm):
    """
    WTForms' SessionSecureform initialized for wikimetrics usage
    """
    SECRET_KEY = app.config['SECRET_KEY']
    TIME_LIMIT = timedelta(hours=2)
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the things required by SessionSecureForm to do its duty
        This __init__ handles the problem with calling SessionSecureForm.__init__()
        outside of a flask request context.
        """
        csrf_context = {}
        # only access the session if we're in a request context
        if current_app:
            csrf_context = session
        
        SessionSecureForm.__init__(self, csrf_context=csrf_context, *args, **kwargs)
    
    def validate_csrf_token(self, field):
        # only validate if we are in a real request context
        if app.config['TESTING']:
            return True
        
        return SessionSecureForm.validate_csrf_token(self, field)
