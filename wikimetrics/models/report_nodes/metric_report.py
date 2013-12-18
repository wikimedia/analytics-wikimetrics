from wikimetrics.configurables import db
from report import ReportLeaf


__all__ = ['MetricReport']


class MetricReport(ReportLeaf):
    """
    Report type responsbile for running a single metric on a project-
    homogenous list of user_ids.  Like all reports, the database session
    is constructed within MetricReport.run()
    """
    
    def __init__(self, metric, user_ids, project):
        super(MetricReport, self).__init__()
        self.metric = metric
        self.user_ids = list(user_ids)
        self.project = project
    
    def run(self):
        session = db.get_mw_session(self.project)
        try:
            result = self.metric(self.user_ids, session)
            return result
        finally:
            session.close()
    
    def __repr__(self):
        return '<MetricReport("{0}")>'.format(self.persistent_id)
