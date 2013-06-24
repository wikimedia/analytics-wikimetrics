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
            response.data,
            """[('Metric', <class 'wikimetrics.metrics.metric.Metric'>), ('NamespaceEdits', <class 'wikimetrics.metrics.namespace_edits.NamespaceEdits'>), ('RandomMetric', <class 'wikimetrics.metrics.dummy.RandomMetric'>), ('RevertRate', <class 'wikimetrics.metrics.revert_rate.RevertRate'>)]""",
            '/metrics should get this temporary, raw list of available metrics, response.data:\n{0}'\
                .format(response.data)
        )
        assert_equal(
            response.data.find('log in with Google'),
            -1,
            '/metrics should get the list of metrics'
        )
