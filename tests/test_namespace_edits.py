from nose.tools import *
from fixtures import DatabaseTest

from wikimetrics.database import Session, MediawikiSession
from wikimetrics.metrics import NamespaceEdits


class NamespaceEditsTest(DatabaseTest):
    
    
    def test_finds_edits():
        assert_true(False)
    
    
    def test_reports_zero_edits():
        assert_true(False)
    
    
    def test_reports_undefined():
        assert_true(False)
