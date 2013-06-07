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
        revisions_by_user = session\
            .query(Revision.rev_user, func.count(Revision.rev_id))\
            .join(Page)\
            .filter(Page.page_namespace == 0)\
            .filter(Revision.rev_user.in_(cohort))\
            .group_by(Revision.rev_user)\
            .all()
        return {r[0]:r[1] for r in revisions_by_user}
