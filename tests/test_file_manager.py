import io
import os
import unittest
import json
from mock import Mock
from nose.tools import assert_equal, raises, assert_true
from logging import RootLogger

from wikimetrics.configurables import app, db, get_absolute_path
from wikimetrics.exceptions import PublicReportIOError
from wikimetrics.api import PublicReportFileManager, COALESCED_REPORT_FILE
from wikimetrics.api.file_manager import _merge_run
from wikimetrics.enums import Aggregation


class PublicReportFileMangerTest(unittest.TestCase):
    """
    Tests should have no side effects. i.e. should not create any files on disk

    If there is a reason why they would they should be cleaned up after

    Assumes /public/static directory is existing, puppet must have created it
    """

    def setUp(self):
        # setup mock logger
        self.logger = Mock(spec=RootLogger)
        self.api = PublicReportFileManager(self.logger, './wikimetrics/')
        self.test_report_path = os.path.join(get_absolute_path(), os.pardir, 'tests')

    def tearDown(self):
        pass

    def test_get_public_report_path(self):
        """
        Path should be constructed acording to protocol
        """
        absolute_report_path = self.api.get_public_report_path('fake-report-id')
        fake_path = 'static/public/fake-report-id.json'
        # should end with 'static/public/fake-report-id.json'
        length = len(fake_path)
        path_len = len(absolute_report_path)
        substr = absolute_report_path[path_len - length:path_len]
        assert_equal(substr, fake_path)

    @raises(PublicReportIOError)
    def test_cannot_write_file(self):
        """
        Correct exception is raised when we cannot write to the
        given path.
        """
        self.api.write_data('/some-fake/path/to-create-file/', 'some-string')

    @raises(PublicReportIOError)
    def test_cannot_remove_file(self):
        """
        Correct exception is raised when we cannot delete a given report
        """
        self.api.remove_file('/some-fake/path/to-delete-file.json')

    def test_coalesce_recurrent_reports(self):
        self.api.root_dir = self.test_report_path
        assert_true(os.path.isdir(self.test_report_path))
        test_report_id = '0000'

        test_report_dir = os.sep.join((self.test_report_path, 'static',
                                      'public', test_report_id))
        full_report = self.api.coalesce_recurrent_reports(test_report_id)

        # Confirm the coalesced file has the correct keys (the "Metric_end_date" for each
        # child report, and that the individual reports in the coalesced file match the
        # content of each child report file
        files_to_coalesce = [f for f in os.listdir(test_report_dir) if os.path.isfile(
            os.sep.join((test_report_dir, f))) and f != COALESCED_REPORT_FILE]

        assert_equal(len(files_to_coalesce), 4)

        report_results = []
        users_reported = set()
        dates = set()
        for f in files_to_coalesce:
            with open(os.sep.join((test_report_dir, f))) as json_file:
                try:
                    loaded = json.load(json_file)
                    for u in loaded['result'][Aggregation.IND]:
                        users_reported.add(u)
                    for d in loaded['result'][Aggregation.AVG]['edits']:
                        dates.add(d)
                    report_results.append(loaded)
                except ValueError:
                    pass

        assert_equal(len(report_results), 3)  # There are 3 valid test report files

        assert_equal({k for k in full_report}, {
            'result', 'parameters'
        })
        assert_equal({k for k in full_report['result']}, {
            Aggregation.AVG, Aggregation.IND
        })
        assert_equal({k for k in full_report['result'][Aggregation.IND]}, users_reported)
        assert_equal({k for k in full_report['result'][Aggregation.AVG]['edits']}, dates)

    @raises(PublicReportIOError)
    def test_remove_recurrent_report(self):
        # Attempt to delete a non-existent recurrent report directory
        self.api.root_dir = self.test_report_path
        test_report_id = '0001'
        self.api.remove_recurrent_report(test_report_id)


class CoalesceTests(unittest.TestCase):
    def test_coalesce_format_initial(self):
        coalesced = {}
        first_run = {
            'result': {
                Aggregation.SUM: {'metric1': 10}
            },
            'parameters': {
                'Metric_timeseries': 'none',
                'Metric_end_date': '2014-07-01'
            }
        }
        _merge_run(coalesced, first_run)
        assert_equal(coalesced, {
            'result': {
                Aggregation.SUM: {'metric1': {'2014-07-01': 10}}
            },
            'parameters': {
                'Metric_timeseries': 'none',
                'Metric_end_date': '2014-07-01'
            }
        })

    def test_coalesce_format_updating(self):
        coalesced = {}
        new_run = {
            'result': {
                Aggregation.IND: {
                    '123|enwiki|1': {
                        'metric1': {
                            '2014-06-14 00:00:00': 0,
                            '2014-06-15 00:00:00': 1,
                            '2014-06-16 00:00:00': 0,
                        },
                        'metric2': {
                            '2014-06-14 00:00:00': 0,
                            '2014-06-15 00:00:00': 0,
                            '2014-06-16 00:00:00': 2,
                        },
                    },
                    '124|enwiki|1': {
                        'metric1': {
                            '2014-06-14 00:00:00': 1,
                            '2014-06-15 00:00:00': 0,
                            '2014-06-16 00:00:00': 1,
                        },
                        'metric2': {
                            '2014-06-14 00:00:00': 0,
                            '2014-06-15 00:00:00': 3,
                            '2014-06-16 00:00:00': 0,
                        },
                    }
                },
                Aggregation.SUM: {
                    'metric1': {
                        '2014-06-14 00:00:00': 1,
                        '2014-06-15 00:00:00': 1,
                        '2014-06-16 00:00:00': 1,
                    },
                    'metric2': {
                        '2014-06-14 00:00:00': 0,
                        '2014-06-15 00:00:00': 3,
                        '2014-06-16 00:00:00': 2,
                    },
                }
            },
            'parameters': {
                'param1': 1,
                'param2': 2,
                'param3': 3,
                'Metric_timeseries': 'day',
            }
        }
        _merge_run(coalesced, new_run)
        assert_equal(coalesced, new_run)

        new_date = '2014-06-17 00:00:00'
        _merge_run(coalesced, {
            'parameters': {'Metric_end_date': new_date},
            'result': {
                Aggregation.SUM: {'metric1': 2, 'metric2': 3},
                Aggregation.IND: {
                    '123|enwiki|1': {'metric1': 3, 'metric2': 1},
                    '124|enwiki|1': {'metric1': 4, 'metric2': 0},
                }
            }
        })
        r = coalesced['result']

        assert_equal(r[Aggregation.SUM]['metric1'][new_date], 2)
        assert_equal(r[Aggregation.SUM]['metric2'][new_date], 3)

        assert_equal(r[Aggregation.IND]['123|enwiki|1']['metric1'][new_date], 3)
        assert_equal(r[Aggregation.IND]['123|enwiki|1']['metric2'][new_date], 1)
        assert_equal(r[Aggregation.IND]['124|enwiki|1']['metric1'][new_date], 4)
        assert_equal(r[Aggregation.IND]['124|enwiki|1']['metric2'][new_date], 0)
