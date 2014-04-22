from nose.tools import assert_equal, assert_true
from tests.fixtures import WebTest, mediawiki_project
from wikimetrics.models import Cohort, CohortUser


class TestDemoController(WebTest):
    
    def test_delete_cohorts(self):
        response = self.app.get('/demo/delete/cohorts/')
        assert_equal(response.status_code, 200)
