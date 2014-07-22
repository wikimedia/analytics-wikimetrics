from wikimetrics.forms import WikimetricsSecureForm
from wikimetrics.models import Revision


class Metric(WikimetricsSecureForm):
    """
    This class is the parent of all Metric implementations.
    Child implementations should be callable and should take in users
    and return the metric computation results for each user.
    In addition, Metric inherits from wtforms Form and therefore child implementations
    can provide WTForms field definitions of their parametrization.
    To enable user interaction with child implementations, Metric also defines some
    class level properties that can be introspected by an interface.
    """
    
    show_in_ui      = False
    id              = None  # unique identifier for client-side use
    
    # this will be displayed as the title of the metric-specific
    # tab in the request form
    label           = None
    description     = None  # basic description of what the metric does
    default_result  = {}    # if results are empty, default to this
    
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

    def filter(self, query, user_ids, column=Revision.rev_user):
        """
        Filters the query by the provided user_ids.
        If user_ids is an empty list, does nothing.

        Parameters
            query       : A sqlalchemy query that may need to be filtered
            user_ids    : A list of user_ids that query should be filtered by
            column      : The sqlalchemy column to filter on.  Defaults to
                          Revision.rev_user, and usually doesn't need to be changed

        Returns
            The same query passed in, with any user_id filters necessary
        """
        if user_ids and len(user_ids):
            query = query.filter(column.in_(user_ids))
        return query
