from nose.tools import *
from tests.fixtures import *


class TestMetricsController(WebTest):
    
    def test_index(self):
        response = self.app.get('/metrics/', follow_redirects=True)
        assert_equal(
            response.status_code,
            200,
            '/metrics should return OK'
        )
        assert_equal(
            response.data.find('log in with Google'),
            -1,
            '/metrics should get the list of metrics'
        )
