from nose.tools import assert_equal
from tests.fixtures import WebTest
import json


class TestDemoController(WebTest):
    
    def test_run_task_in_celery(self):
        response = self.app.get('/demo/metric/random/1')
        print response.data
        assert_equal(
            response.status_code, 200,
            '/demo/metric/random/<cohort-id>/ exists and is OK to GET'
        )
    
    def test_add_demo_cohorts(self):
        response = self.app.get('/demo/create/cohorts/')
        assert_equal(
            response.status_code, 200,
            '/demo/create/cohorts/ exists and is OK to GET'
        )
        assert_equal(
            response.data, 'OK, wiped out the database and added cohorts only for test@test.com',
            '/demo/create/cohorts/ completes successfully'
        )
