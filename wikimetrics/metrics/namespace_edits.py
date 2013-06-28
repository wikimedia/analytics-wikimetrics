from flask.ext import wtf
from sqlalchemy import func
from metric import Metric
from wikimetrics.models import Page, Revision
import logging
logger = logging.getLogger(__name__)

__all__ = [
    'NamespaceEdits',
]


class NamespaceEdits(Metric):
    """
    This class implements namespace edits logic.
    An instance of the class is callable and will compute the number of edits
    for each user in a passed-in list.
    
    This sql query was used as a starting point for the sqlalchemy query:
    
     select r.rev_user, r.count(*)
       from revision r
                inner join
            page p      on p.page_id = r.rev_page
      where r.rev_timestamp between [start] and [end]
        and r.rev_user in ([parameterized])
        and p.page_namespace in ([parameterized])
      group by rev_user
    """
    
    show_in_ui  = True
    id          = 'edits'
    label       = 'Edits'
    description = 'Compute the number of edits in a specific namespace of a mediawiki project'
    
    namespaces = wtf.IntegerField(default=0, description='0, 2, 4, etc.')
    
    def __call__(self, user_ids, session):
        """
        Parameters:
            user_ids    : list of mediawiki user ids to find edit for
            session     : sqlalchemy session open on a mediawiki database
        
        Returns:
            dictionary from user ids to the number of edit found.
        """
        # directly construct dict from query results
        logger.debug('user_ids: %s, namespaces: %s', user_ids, self.namespaces)
        revisions_by_user = dict(
            session
            .query(Revision.rev_user, func.count(Revision.rev_id))
            .join(Page)
            .filter(Page.page_namespace.in_(self.namespaces))
            .filter(Revision.rev_user.in_(user_ids))
            .group_by(Revision.rev_user)
            .all()
        )
        return {user_id: revisions_by_user.get(user_id, 0) for user_id in user_ids}
