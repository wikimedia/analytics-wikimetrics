from mock import Mock
from logging import RootLogger
from nose.tools import assert_equals, raises
from ..fixtures import DatabaseTest

from wikimetrics.models import ReportStore
from wikimetrics.exceptions import UnauthorizedReportAccessError
from wikimetrics.api import PublicReportFileManager
from wikimetrics.exceptions import PublicReportIOError


class ReportStoreTest(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self.reports = [
            ReportStore(public=False, recurrent=False, user_id=1),
            ReportStore(public=True, recurrent=False, user_id=1),
            ReportStore(public=False, recurrent=True, user_id=1),
            ReportStore(public=True, recurrent=True, user_id=1),
        ]
        self.session.add_all(self.reports)
        self.session.commit()
    
    def test_update_reports_public_true(self):
        r = ReportStore.update_reports(
            [self.reports[0].id, self.reports[1].id], 1, public=True
        )
        assert_equals(r, True)
        self.session.commit()
        self.session.expire_all()
        
        assert_equals(self.reports[0].public, True)
        assert_equals(self.reports[1].public, True)
        assert_equals(self.reports[2].public, False)
        assert_equals(self.reports[3].public, True)
        assert_equals(self.reports[0].recurrent, False)
        assert_equals(self.reports[1].recurrent, False)
        assert_equals(self.reports[2].recurrent, True)
        assert_equals(self.reports[3].recurrent, True)
    
    def test_update_reports_public_false(self):
        r = ReportStore.update_reports(
            [self.reports[0].id, self.reports[1].id], 1, public=False
        )
        assert_equals(r, True)
        self.session.commit()
        self.session.expire_all()
        
        assert_equals(self.reports[0].public, False)
        assert_equals(self.reports[1].public, False)
        assert_equals(self.reports[2].public, False)
        assert_equals(self.reports[3].public, True)
        assert_equals(self.reports[0].recurrent, False)
        assert_equals(self.reports[1].recurrent, False)
        assert_equals(self.reports[2].recurrent, True)
        assert_equals(self.reports[3].recurrent, True)
    
    def test_update_reports_recurrent_true(self):
        r = ReportStore.update_reports(
            [self.reports[0].id, self.reports[2].id], 1, recurrent=True
        )
        assert_equals(r, True)
        self.session.commit()
        self.session.expire_all()
        
        assert_equals(self.reports[0].public, False)
        assert_equals(self.reports[1].public, True)
        assert_equals(self.reports[2].public, False)
        assert_equals(self.reports[3].public, True)
        assert_equals(self.reports[0].recurrent, True)
        assert_equals(self.reports[1].recurrent, False)
        assert_equals(self.reports[2].recurrent, True)
        assert_equals(self.reports[3].recurrent, True)
    
    def test_update_reports_recurrent_false(self):
        r = ReportStore.update_reports(
            [self.reports[0].id, self.reports[2].id], 1, recurrent=False
        )
        assert_equals(r, True)
        self.session.commit()
        self.session.expire_all()
        
        assert_equals(self.reports[0].public, False)
        assert_equals(self.reports[1].public, True)
        assert_equals(self.reports[2].public, False)
        assert_equals(self.reports[3].public, True)
        assert_equals(self.reports[0].recurrent, False)
        assert_equals(self.reports[1].recurrent, False)
        assert_equals(self.reports[2].recurrent, False)
        assert_equals(self.reports[3].recurrent, True)
    
    @raises(UnauthorizedReportAccessError)
    def test_update_another_users_reports(self):
        # updating with the wrong user_id does not work
        r = ReportStore.update_reports(
            [self.reports[1].id], 0, recurrent=True
        )
        assert_equals(r, False)
        self.session.commit()
        self.session.expire_all()
        
    def test_make_private_report(self):
        """
        Making a report private should try to delete it
        """
        file_manager = Mock(spec=PublicReportFileManager)
        report_path = file_manager.get_public_report_path(self.reports[0].id)
        ReportStore.make_report_private(
            self.reports[0].id, self.reports[0].user_id, file_manager
        )
        file_manager.remove_file.assert_called_with(report_path)
    
    @raises(PublicReportIOError)
    def test_public_report_state_change_error(self):
        """
        Persistent Report should propagate IO errors from
        PublicReportFileManager
        """
        self.app = Mock()
        
        self.logger = Mock(spec=RootLogger)
        
        file_manager = PublicReportFileManager(self.logger, '/some/fake/absolute/path')
        file_manager.write_data = Mock(side_effect=PublicReportIOError('Boom!'))
        # do not write anything to disk
        file_manager.get_public_report_path = Mock()
        ReportStore.make_report_public(
            self.reports[0].id, self.reports[0].user_id, file_manager, 'testing data'
        )
