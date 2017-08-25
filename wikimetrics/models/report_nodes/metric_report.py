from wikimetrics.configurables import db
from report import ReportLeaf
from wikimetrics.models.storage.wikiuser import WikiUserKey
from wikimetrics.utils import NO_RESULTS


class MetricReport(ReportLeaf):
    """
    Report type responsbile for running a single metric on a project-
    homogenous list of user_ids.  Like all reports, the database session
    is constructed within MetricReport.run()
    """
    
    def __init__(self, metric, cohort_id, user_ids, project, *args, **kwargs):
        """
        Parameters:
            metric  : an instance of a Metric class
            cohort  : a logical cohort object
            args    : should include any parameters needed by ReportNode
            kwargs  : should include any parameters needed by ReportNode
        """
        super(MetricReport, self).__init__(*args, **kwargs)
        self.metric = metric
        if user_ids is not None:
            self.user_ids = list(user_ids)
        else:
            self.user_ids = None
        self.cohort_id = cohort_id
        self.project = project

    def run(self):
        session = db.get_mw_session(self.project)
        results_by_user = self.metric(self.user_ids, session)
        results = {
            str(WikiUserKey(key, self.project, self.cohort_id)) : value
            for key, value in results_by_user.items()
        }
        if not len(results):
            results = {NO_RESULTS : self.metric.default_result}
        return results
