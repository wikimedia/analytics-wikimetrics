from nose.tools import assert_equal, raises
from sqlalchemy.orm.exc import NoResultFound

from wikimetrics.models import Cohort, WikiUser
from ..fixtures import DatabaseTest


class CohortTest(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self.common_cohort_1()
    
    def test_iter(self):
        user_ids = list(self.cohort)
        assert_equal([e.user_id for e in self.editors], user_ids)
    
    def test_empty_iter(self):
        self.cohort.validated = False
        self.session.commit()
        
        user_ids = list(self.cohort)
        assert_equal(user_ids, [])
    
    def test_iter_with_invalid(self):
        wikiusers = self.session.query(WikiUser).all()
        wikiusers[0].valid = False
        wikiusers[1].valid = None
        self.session.commit()
        
        user_ids = list(self.cohort)
        assert_equal(wikiusers[0].mediawiki_userid in user_ids, False)
        assert_equal(wikiusers[1].mediawiki_userid in user_ids, False)
        assert_equal(wikiusers[2].mediawiki_userid in user_ids, True)
        assert_equal(wikiusers[3].mediawiki_userid in user_ids, True)
        assert_equal(len(user_ids), 2)
    
    def test_group_by_project(self):
        wikiusers = self.session.query(WikiUser).all()
        print [(w.mediawiki_userid, w.valid, w.mediawiki_username) for w in wikiusers]
        wikiusers[0].valid = False
        wikiusers[1].valid = None
        self.session.commit()
        
        user_ids = []
        for project, uids in self.cohort.group_by_project():
            user_ids += list(uids)
        
        assert_equal(wikiusers[0].mediawiki_userid in user_ids, False)
        assert_equal(wikiusers[1].mediawiki_userid in user_ids, False)
        assert_equal(wikiusers[2].mediawiki_userid in user_ids, True)
        assert_equal(wikiusers[3].mediawiki_userid in user_ids, True)
        assert_equal(len(user_ids), 2)
    
    def test_get_safely(self):
        c = Cohort.get_safely(self.session, self.owner_user_id, by_id=self.cohort.id)
        assert_equal(c.name, self.cohort.name)
        c = Cohort.get_safely(self.session, self.owner_user_id, by_name=self.cohort.name)
        assert_equal(c.id, self.cohort.id)
    
    @raises(NoResultFound)
    def test_get_safely_raises_exception_for_not_found_by_id(self):
        c = Cohort.get_safely(self.session, self.owner_user_id, by_id=0)
        assert_equal(c, None)
    
    @raises(NoResultFound)
    def test_get_safely_raises_exception_for_not_found_by_name(self):
        c = Cohort.get_safely(self.session, self.owner_user_id, by_name='')
        assert_equal(c, None)
