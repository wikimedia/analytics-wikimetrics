from wikimetrics.configurables import db
from report import ReportLeaf
from wikimetrics.models.wikiuser import WikiUserKey


__all__ = ['MetricReport']


class MetricReport(ReportLeaf):
    """
    Report type responsbile for running a single metric on a project-
    homogenous list of user_ids.  Like all reports, the database session
    is constructed within MetricReport.run()
    """
    
    def __init__(self, metric, cohort_id, user_ids, project, *args, **kwargs):
        super(MetricReport, self).__init__(*args, **kwargs)
        self.metric = metric
        self.user_ids = list(user_ids)
        self.cohort_id = cohort_id
        self.project = project

    def run(self):
        session = db.get_mw_session(self.project)
        try:
            results_by_user = self.metric(self.user_ids, session)
            return {
                str(WikiUserKey(key, self.project, self.cohort_id)) : value
                for key, value in results_by_user.items()
            }
        finally:
            session.close()
    
    def __repr__(self):
        return '<MetricReport("{0}")>'.format(self.persistent_id)
