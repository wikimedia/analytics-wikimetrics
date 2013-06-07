from sqlalchemy import func
from metric import Metric
from wikimetrics.database import MediawikiSession
from wikimetrics.models import *

__all__ = [
    'NamespaceEdits',
]

class NamespaceEdits(Metric):
    
    def __call__(self, cohort):
        mwSession = MediawikiSession()
        revisions_by_user = mwSession\
            .query(Revision.rev_user, func.count(Revision.rev_id))\
            .join(Page)\
            .filter(Page.page_namespace == 0)\
            .filter(Revision.rev_user.in_(cohort))\
            .group_by(Revision.rev_user)\
            .all()
        return {r[0]:r[1] for r in revisions_by_user}
