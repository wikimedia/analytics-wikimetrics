from nose.tools import *
from fixtures import DatabaseTest

from wikimetrics.database import Session, get_mw_session
from wikimetrics.metrics import NamespaceEdits
from wikimetrics.models import Cohort


class NamespaceEditsTest(DatabaseTest):
    def setUp(self):
        super(NamespaceEditsTest, self).setUp()
        mwSession = get_mw_session('enwiki')
        #TODO: add data for metric to find
        #mwSession.add(Revision(page_id=1,rev_user=
    
    def test_finds_edits(self):
        session = Session()
        cohort = session.query(Cohort).filter_by(name='test').one()
        
        metric = NamespaceEdits()
        results = metric(cohort)
        
        assert_true(results is not None)
        assert_true(results['1'] == 2, 'Dan had not 2 edits')
        assert_true(results['2'] == 3, 'Evan had not 3 edits')
    
    
    def test_reports_zero_edits(self):
        session = Session()
        cohort = session.query(Cohort).filter_by(name='test').one()
        
        metric = NamespaceEdits()
        results = metric(cohort)
        
        assert_true(results is not None)
        assert_true(results['3'] == 0, 'Andrew had not 0 edits')
    
    
    def test_reports_undefined(self):
        session = Session()
        cohort = session.query(Cohort).filter_by(name='test').one()
        
        metric = NamespaceEdits()
        results = metric(cohort)
        
        assert_true(results is not None)
        assert_true(results['4'] is None, 'Diederik had not undefined edits')
