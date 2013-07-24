from wtforms.ext.csrf.session import SessionSecureForm
from wikimetrics.configurables import app
import logging
logger = logging.getLogger(__name__)

__all__ = [
    'Metric',
]


class Metric(SessionSecureForm):
    """
    This class is the parent of all Metric implementations.
    Child implementations should be callable and should take in users
    and return the metric computation results for each user.
    In addition, Metric inherits from wtforms Form and therefore child implementations
    can provide WTForms field definitions of their parametrization.
    To enable user interaction with child implementations, Metric also defines some
    class level properties that can be introspected by an interface.
    """
    
    show_in_ui  = False
    id          = None  # unique identifier for client-side use
    label       = None  # this will be displayed as the title of the metric-specific
                        # tab in the request form
    description = None  # basic description of what the metric does
    
    def __call__(self, user_ids, session):
        """
        This is the __call__ signature any child implementations should follow.
        
        Parameters:
            user_ids    : list of mediawiki user ids to calculate the metric on
            session     : sqlalchemy session open on a mediawiki database
        
        Returns:
            dictionary from user ids to the metric results.
        """
        return {user: None for user in user_ids}
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the things required by SessionSecureForm to do its duty
        This __init__ handles the problem with calling SessionSecureForm.__init__()
        outside of a flask request context.
        """
        self.SECRET_KEY = 'not really secret, this will only happen in a testing context'
        csrf_context = {}
        
        if app:
            # TODO: need to set csrf_context to something? (the flask session maybe?)
            self.SECRET_KEY = app.config['SECRET_KEY']
        
        SessionSecureForm.__init__(self, csrf_context=csrf_context, *args, **kwargs)
