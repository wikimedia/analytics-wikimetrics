from nose.tools import *
from tests.fixtures import *
import json
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


class TestJobsController(WebTest):
    
    def test_index(self):
        response = self.app.get('/jobs/', follow_redirects=True)
        assert_true(
            response._status_code == 200,
            '/jobs should get the list of jobs for the current user'
        )
    
    def test_list(self):
        response = self.app.get('/jobs/list', follow_redirects=True)
        expected = """{
  "jobs": [
    {
      "status": "CREATED",
      "classpath": "",
      "user_id": 2,
      "id": 2,
      "result_id": null
    },
    {
      "status": "STARTED",
      "classpath": "",
      "user_id": 2,
      "id": 3,
      "result_id": null
    },
    {
      "status": "STARTED",
      "classpath": "",
      "user_id": 2,
      "id": 4,
      "result_id": null
    },
    {
      "status": "FINISHED",
      "classpath": "",
      "user_id": 2,
      "id": 5,
      "result_id": null
    }
  ]
}"""
        assert_equal(
            response.data,
            expected,
            '/jobs/list should return a list of job objects, but instead returned:\n{0}'\
                .format(response.data)
        )
