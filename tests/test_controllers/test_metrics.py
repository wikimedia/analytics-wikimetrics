from nose.tools import *
from tests.fixtures import *


class TestMetricsController(WebTest):
    
    def test_index(self):
        response = self.app.get('/metrics/')
        assert_true(
            response._status_code == 200,
            '/metrics should get the list of metrics'
        )
