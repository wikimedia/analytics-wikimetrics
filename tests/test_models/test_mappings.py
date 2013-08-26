from nose.tools import assert_true, assert_equals, assert_equal
import celery
from wikimetrics.models import (
    PersistentReport,
    User,
    UserRole,
    Cohort,
    CohortUser,
    CohortUserRole,
    CohortWikiUser,
    WikiUser,
    Logging,
    Page,
    MediawikiUser,
    Revision,
)
from tests.fixtures import DatabaseTest


class TestMappings(DatabaseTest):
    #***********
    # Mapping tests for our custom tables
    #***********

    def test_report(self):
        j = self.session.query(PersistentReport).get(self.test_report_id)
        assert_true(j.status == celery.states.PENDING)
    
    def test_user(self):
        u = self.session.query(User).get(self.test_user_id)
        assert_true(u.username == 'Dan')
        assert_true(u.role == UserRole.GUEST)
    
    def test_wikiuser(self):
        wu = self.session.query(WikiUser).get(self.test_wiki_user_id)
        assert_equals(wu.mediawiki_username, 'Dan')
    
    def test_cohort(self):
        c = self.session.query(Cohort).get(self.test_cohort_id)
        assert_equals(c.name, 'test')
        assert_true(c.public is False)
        
    def test_cohort_user(self):
        cu = self.session.query(CohortUser).get(self.test_cohort_user_id)
        assert_equals(cu.user_id, self.test_user_id)
        assert_equals(cu.cohort_id, self.test_cohort_id)
    
    def test_cohort_wikiuser(self):
        cwu = self.session.query(CohortWikiUser).get(self.test_cohort_wiki_user_id)
        assert_equals(cwu.wiki_user_id, self.test_wiki_user_id)
        assert_equals(cwu.cohort_id, self.test_cohort_id)
    
    #***********
    # Mapping tests for mediawiki tables
    #***********
    def test_mediawiki_logging(self):
        row = self.mwSession.query(Logging).get(self.test_logging_id)
        assert_equals(row.log_user_text, 'Reedy')
    
    def test_mediawiki_user(self):
        row = self.mwSession.query(MediawikiUser).get(self.test_mediawiki_user_id)
        assert_equals(row.user_name, 'Dan')
    
    def test_mediawiki_page(self):
        row = self.mwSession.query(Page).get(self.test_page_id)
        assert_equals(row.page_title, 'Main_Page')
    
    def test_mediawiki_revision(self):
        row = self.mwSession.query(Revision).get(self.test_revision_id)
        assert_equals(row.rev_comment, 'Dan edit 1')
    
    #***********
    # Join tests
    #***********
    def test_cohort_members(self):
        user_ids = self.session\
            .query(WikiUser.mediawiki_userid)\
            .join(CohortWikiUser)\
            .filter(CohortWikiUser.cohort_id == self.test_cohort_id)\
            .all()
        
        assert_equal(len(user_ids), 4)
    
    def test_cohort_ownership(self):
        cohorts = self.session\
            .query(Cohort)\
            .join(CohortUser)\
            .join(User)\
            .filter(CohortUser.role == CohortUserRole.OWNER)\
            .filter(User.username == 'Evan')\
            .all()
        print cohorts
        assert_equal(len(cohorts), 2, "User Evan should own 2 cohorts")
    
    #***********
    # String representation tests
    #***********
    def test_report_repr(self):
        r = self.session.query(PersistentReport).get(self.test_report_id)
        assert_true(str(r).find('PersistentReport') >= 0)
    
    def test_user_repr(self):
        u = self.session.query(User).get(self.test_user_id)
        assert_true(str(u).find('User') >= 0)
    
    def test_cohort_repr(self):
        c = self.session.query(Cohort).get(self.test_cohort_id)
        assert_true(str(c).find('Cohort') >= 0)
    
    def test_cohort_user_repr(self):
        cu = self.session.query(CohortUser).get(self.test_cohort_user_id)
        assert_true(str(cu).find('CohortUser') >= 0)
    
    def test_wikiuser_repr(self):
        wu = self.session.query(WikiUser).get(self.test_wiki_user_id)
        assert_true(str(wu).find('WikiUser') >= 0)
    
    def test_cohort_wikiuser_repr(self):
        cwu = self.session.query(CohortWikiUser).get(self.test_cohort_wiki_user_id)
        assert_true(str(cwu).find('CohortWikiUser') >= 0)
