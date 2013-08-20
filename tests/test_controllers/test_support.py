from nose.tools import assert_equal, assert_true
from tests.fixtures import WebTest


class TestSupportController(WebTest):
    
    def test_index(self):
        response = self.app.get('/', follow_redirects=True)
        assert_equal(
            response._status_code, 200,
            '/ should get the support page'
        )

        assert_true(response.data.find('Mailing list') >= 0)
