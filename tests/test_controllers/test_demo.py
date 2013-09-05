from nose.tools import assert_equal, assert_true
from tests.fixtures import WebTest
from wikimetrics.models import Cohort, CohortUser


class TestDemoController(WebTest):
    
    def test_run_task_in_celery(self):
        response = self.app.get('/demo/metric/random/1')
        assert_equal(
            response.status_code, 200,
            '/demo/metric/random/<cohort-id>/ exists and is OK to GET'
        )
        
        response = self.app.get('/demo/metric/random/2')
        assert_equal(
            response.status_code, 200,
            '/demo/metric/random/<cohort-without-users> works'
        )
    
    def test_delete_cohorts(self):
        response = self.app.get('/demo/delete/cohorts/')
        assert_equal(response.status_code, 200)
    
    def test_add_demo_cohorts(self):
        response = self.app.get('/demo/create/cohorts/')
        assert_equal(
            response.status_code, 200,
            '/demo/create/cohorts/ exists and is OK to GET'
        )
        assert_equal(
            response.data,
            'OK, wiped out the database and added cohorts only for test@test.com',
            '/demo/create/cohorts/ completes successfully'
        )
