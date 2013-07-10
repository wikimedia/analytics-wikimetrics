from wikimetrics.models import Cohort, JobResponse
from wikimetrics.metrics import NamespaceEdits
from ..fixtures import QueueDatabaseTest
from nose.tools import assert_equals
import logging

logger = logging.getLogger(__name__)


class JobResponseTest(QueueDatabaseTest):
    
    def test_empty_response(self):
        # TODO: handle case where user tries to submit form with no cohorts / metrics
        jr = JobResponse(cohort_metrics=[], user_id=0)
        result = jr.task.delay().get()
        assert_equals(result, [])
    
    
    def test_basic_response(self):
        c = self.session.query(Cohort).filter_by(name='test').one()
        m = NamespaceEdits(namespaces=[0,1,2])
        
        jr = JobResponse(cohort_metrics=[(c,m)], user_id=0)
        results = jr.task.delay().get()
        print results
