import io
import os
import unittest
from mock import Mock
from nose.tools import assert_equals, raises
from logging import RootLogger

from wikimetrics.configurables import app, db
from wikimetrics.exceptions import PublicReportIOError
from wikimetrics.api import PublicReportFileManager


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
        assert_equals(substr, fake_path)
    
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
