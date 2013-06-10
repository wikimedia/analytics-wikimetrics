from sqlalchemy import func
from metric import Metric
from wikimetrics.models import *

__all__ = [
    'NamespaceEdits',
]

class NamespaceEdits(Metric):
    
    def __init__(self, namespaces=[0]):
        self.namespaces = namespaces

    def __call__(self, user_ids, session):
        revisions_by_user = dict(session\
            .query(Revision.rev_user, func.count(Revision.rev_id))\
            .join(Page)\
            .filter(Page.page_namespace in self.namespaces)\
            .filter(Revision.rev_user.in_(user_ids))\
            .group_by(Revision.rev_user)\
            .all())
        #return {user_id : r[1] for r in revisions_by_user}
        # make sure we return zero when user has no revisions
        # we could solve this with temporary tables in the future
        return {user_id : revisions_by_user.get(user_id, 0) for user_id in user_ids}
        
