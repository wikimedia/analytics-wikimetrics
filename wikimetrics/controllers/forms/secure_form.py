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
        # do not validate csrf if we are running tests
        self.no_csrf = 'TESTING' in app.config and app.config['TESTING'] is True
        
        csrf_context = {}
        # only access the session if we're in a request context
        if current_app:
            csrf_context = session
        
        SessionSecureForm.__init__(self, csrf_context=csrf_context, *args, **kwargs)
    
    def validate_csrf_token(self, field):
        return self.no_csrf or SessionSecureForm.validate_csrf_token(self, field)
    
    def disable_csrf(self):
        """
        Makes calls to validate_csrf_token always return True.  Useful for scheduled
        report runs when the metric is not configured on a form.
        """
        self.no_csrf = True
