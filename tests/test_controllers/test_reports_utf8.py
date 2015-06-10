# -*- coding: utf-8 -*-
import json
from nose.tools import assert_true, assert_equal
from tests.fixtures import WebTest


class ReportsControllerUTF8Test(WebTest):

    def test_create_report_from_cohort_with_utf8_description(self):
        '''
        Tests the encoding conversion of the cohort description field.
        Note the first line of this file.
        '''
        desired_responses = [{
            'name': 'Edits - test',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
                'description': 'شديدة'
            },
            'metric': {
                'name': 'NamespaceEdits',
                'namespaces': [0, 1, 2],
                'start_date': '2013-06-01 00:00:00',
                'end_date': '2013-09-01 00:00:00',
                'individualResults': True,
                'aggregateResults': True,
                'aggregateSum': True,
                'aggregateAverage': True,
                'aggregateStandardDeviation': True,
            },
        }]
        json_to_post = json.dumps(desired_responses)
        response = self.client.post('/reports/create/', data=dict(
            responses=json_to_post
        ))

        # Just make sure that it does not crash
        assert_equal(response.status_code, 200)
        assert_true(response.data.find('isRedirect') >= 0)
        assert_true(response.data.find('/reports/') >= 0)
