import io
import os
import unittest
import json
from mock import Mock
from nose.tools import assert_equal, raises, assert_false, assert_true
from logging import RootLogger

from wikimetrics.configurables import app, db, get_absolute_path
from wikimetrics.exceptions import PublicReportIOError
from wikimetrics.api import PublicReportFileManager
from wikimetrics.api import COALESCED_REPORT_FILE


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
        l = len(fake_path)
        path_len = len(absolute_report_path)
        substr = absolute_report_path[path_len - l:path_len]
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
        for f in files_to_coalesce:
            with open(os.sep.join((test_report_dir, f))) as json_file:
                try:
                    report_results.append(json.load(json_file))
                except ValueError:
                    pass

        assert_equal(len(report_results), 3)  # There are 3 valid test report files

        expected_end_dates = {r['parameters']['Metric_end_date'] for r in report_results}
        expected_values = [r['result'] for r in report_results]

        actual_end_dates = {k for k, v in full_report.items() if k != 'parameters'}
        actual_values = [v for k, v in full_report.items() if k != 'parameters']

        assert_equal(expected_end_dates, actual_end_dates)
        assert_equal(sorted(expected_values), sorted(actual_values))

    @raises(PublicReportIOError)
    def test_remove_recurrent_report(self):
        # Attempt to delete a non-existent recurrent report directory
        self.api.root_dir = self.test_report_path
        test_report_id = '0001'
        self.api.remove_recurrent_report(test_report_id)
