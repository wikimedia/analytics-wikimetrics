import json
from nose.tools import assert_equal, assert_not_equal
from tests.fixtures import WebTest


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
        assert_not_equal(
            response.data.find('BytesAdded'), -1,
            'BytesAdded detail should be displayed'
        )
        assert_not_equal(
            response.data.find('NamespaceEdits'), -1,
            'NamespaceEdits detail should be displayed'
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
            response.data.find('name="positive_only_sum"'),
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
    
    def test_configure_namespaces_post(self):
        response = self.app.post('/metrics/configure/NamespaceEdits', data=dict(
            namespaces='abcd',
        ))
        print response.data
        assert_not_equal(
            response.data.find('<li class="text-error">'),
            -1,
            'Validation on the NamespaceEdits configuration, '
            'namespaces field is not happening.'
        )
