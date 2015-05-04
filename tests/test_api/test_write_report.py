from nose.tools import assert_equals, assert_true, raises
from celery.exceptions import SoftTimeLimitExceeded
import unittest
import os
from datetime import date
# needed for mock logger
from mock import Mock, MagicMock
from logging import RootLogger, getLogger
from wikimetrics.api.batch import WriteReportTask, COALESCED_REPORT_FILE
from wikimetrics.api import PublicReportFileManager
from wikimetrics.exceptions import PublicReportIOError
from wikimetrics.utils import json_string


class WriteReportTaskTest(unittest.TestCase):
    
    def setUp(self):
        logger = Mock(spec=RootLogger)
        self.results = {'results': 'good'}
        self.fake_path = '/fake/fake/path/'
        file_manager = PublicReportFileManager(logger, '/some/fake/absolute/path')
        file_manager.write_data = Mock()
        file_manager.remove_file = Mock()
        file_manager.get_public_report_path = MagicMock(return_value=self.fake_path)
        file_manager.coalesce_recurrent_reports = MagicMock(return_value=self.results)
        file_manager.remove_old_report_files = MagicMock()
        self.file_manager = file_manager
    
    def test_happy_case(self):
        """
        Create a report on disk
        """
        today = date.today()
        concatenated_report_filepath = os.path.join(self.fake_path,
                                                    COALESCED_REPORT_FILE)
        wr = WriteReportTask('123', today, self.results, self.file_manager)
        wr.run()
        assert_equals(self.file_manager.write_data.call_count, 2)
        assert_equals(self.file_manager.get_public_report_path.call_count, 1)
        assert_equals(self.file_manager.coalesce_recurrent_reports.call_count, 1)
        assert_equals(self.file_manager.remove_old_report_files.call_count, 1)
        self.file_manager.write_data.assert_called_with(concatenated_report_filepath,
                                                        json_string(self.results))
    
    @raises(PublicReportIOError)
    def test_problems_writing(self):
        """
        Exception is thrown when we cannot write to the directory
        """
        self.file_manager.write_data = Mock(side_effect=PublicReportIOError('Boom!'))
        wr = WriteReportTask('12345', date.today(), self.results, self.file_manager)
        wr.run()
    
    @raises(Exception)
    def test_no_problems_writing(self):
        """
        Exception is thrown when we pass a bad created date
        """
        wr = WriteReportTask('12345', '', self.results)
        wr.run()
