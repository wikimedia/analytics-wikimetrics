from wikimetrics.models import Cohort, RunReport, MultiProjectMetricReport
from wikimetrics.metrics import NamespaceEdits
from ..fixtures import QueueDatabaseTest
from nose.tools import assert_equals


class RunReportTest(QueueDatabaseTest):
    
    def test_empty_response(self):
        # TODO: handle case where user tries to submit form with no cohorts / metrics
        jr = RunReport([], user_id=self.test_user_id)
        result = jr.task.delay().get()
        assert_equals(result, [])
    
    def test_basic_response(self):
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.test_cohort_id,
            },
            'metric': {
                'name': 'NamespaceEdits',
                'namespaces': '0,1,2',
            },
        }]
        jr = RunReport(desired_responses, user_id=self.test_user_id)
        results = jr.task.delay().get().result[0].result
        # TODO: figure out why one of the resulting wiki_user_ids is None here
        print results
        assert_equals(
            len(results),
            4,
        )
