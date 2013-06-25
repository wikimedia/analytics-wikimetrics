import pprint
from nose.tools import *
from tests.fixtures import *


class TestCohortsController(WebTest):
    
    def test_index(self):
        response = self.app.get('/cohorts/', follow_redirects=True)
        assert_equal(
            response._status_code, 200,
            '/cohorts should get the list of cohorts'
        )
    
    def test_list(self):
        response = self.app.get('/cohorts/list', follow_redirects=True)
        expected = """{
  "cohorts": [
    {
      "default_project": null,
      "description": null,
      "created": null,
      "changed": null,
      "enabled": true,
      "public": true,
      "id": 1,
      "name": "test"
    }
  ]
}"""
        assert_equal(
            response.data,
            expected,
            '/cohorts/list should return a json list of cohort objects, but instead returned:\n{0}'\
                .format(response.data)
        )
