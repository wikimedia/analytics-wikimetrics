from datetime import datetime, timedelta

from wikimetrics.configurables import db
from wikimetrics.models import Revision


class ReplicationLagService():
    """Service to check replication lag of databases"""

    def __init__(self, mw_projects=None, lag_threshold=None):
        """
        Construct service to check database replication lag

        Parameters:
            mw_projects   : List of MediaWiki projects to check against
                replication lag. If None, then REPLICATION_LAG_MW_PROJECTS from
                the database configuration gets used. If that is unset, [] is
                used. (default: None)
            lag_threshold : time period. If the most recent edit in a wiki is
                older than this time period, the wiki's database is considered
                to be lagging. If None, then REPLICATION_LAG_THRESHOLD from the
                database configuration gets used. If that is unset, '3 hours'
                gets used. (default: None)
        """
        self._mw_projects = mw_projects
        if self._mw_projects is None:
            self._mw_projects = db.config.get('REPLICATION_LAG_MW_PROJECTS', [])

        self._lag_threshold = lag_threshold
        if self._lag_threshold is None:
            self._lag_threshold = timedelta(hours=db.config.get(
                'REPLICATION_LAG_THRESHOLD', 3))

    def _is_mw_project_lagged(self, mw_project):
        """
        Determines whether the given wiki is considered lagged or not.

        Parameters:
            mw_project: Name of the wiki to check.
        """
        session = db.get_mw_session(mw_project)
        timestamp = session.query(Revision.rev_timestamp)\
            .order_by(Revision.rev_timestamp.desc())\
            .limit(1)\
            .scalar()
        session.close()

        return timestamp is None or \
            timestamp < datetime.now() - self._lag_threshold

    def is_any_lagged(self):
        """
        Determines whether any of the default projects are considered lagged or
        not.
        """
        return any(self._is_mw_project_lagged(p) for p in self._mw_projects)
