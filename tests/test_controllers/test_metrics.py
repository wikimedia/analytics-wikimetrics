import json
from nose.tools import assert_equal, assert_not_equal, assert_true
from tests.fixtures import WebTest


class TestMetricsController(WebTest):
    
    def test_index(self):
        response = self.app.get('/metrics/', follow_redirects=True)
        assert_equal(
            response.status_code,
            200,
            '/metrics should return OK'
        )
        metrics_dictionary = json.loads(response.data)
        assert_true(
            'BytesAdded' in metrics_dictionary['metrics'],
            '/metrics should get this temporary, raw list of available metrics, '
            'response.data:\n{0}'.format(response.data)
        )
        assert_equal(
            response.data.find('log in with Google'),
            -1,
            '/metrics should get the list of metrics'
        )
    
    def test_list(self):
        response = self.app.get('/metrics/list/', follow_redirects=True)
        parsed = json.loads(response.data)
        assert_equal(
            len(filter(lambda m : m['name'] == 'BytesAdded', parsed['metrics'])),
            1,
            'test. got: {0}'.format(parsed)
        )
    
    def test_configure_get(self):
        response = self.app.get('/metrics/configure/BytesAdded')
        assert_not_equal(
            response.data.find('name="positive_total"'),
            -1,
            'A form to configure a BytesAdded metric was not rendered'
        )
    
    def test_configure_post(self):
        response = self.app.post('/metrics/configure/BytesAdded', data=dict(
            start_date='hi'
        ))
        assert_not_equal(
            response.data.find('<li class="text-error">Not a valid date value</li>'),
            -1,
            'Validation on a BytesAdded configuration is not happening'
        )
