from nose.tools import *
from wikimetrics.database import init_db, Session, get_mw_session
from wikimetrics.models import *
from tests.fixtures import *


class TestMappings(DatabaseTest):
    #***********
    # Mapping tests for our custom tables
    #***********

    def test_job(self):
        j = self.session.query(Job).get(1)
        assert_true(j.status == JobStatus.CREATED)
    
    def test_user(self):
        u = self.session.query(User).get(1)
        assert_true(u.username == 'Dan')
        assert_true(u.role == UserRole.GUEST)
    
    def test_wikiuser(self):
        wu = self.session.query(WikiUser).get(1)
        assert_true(wu.mediawiki_username == 'Dan')
    
    def test_cohort(self):
        c = self.session.query(Cohort).get(1)
        assert_true(c.name == 'test')
        assert_true(c.public is False)
    
    def test_cohort_wikiuser(self):
        cwu = self.session.query(CohortWikiUser).get(1)
        assert_true(cwu.wiki_user_id == 1)
        assert_true(cwu.cohort_id == 1)
    
    #***********
    # Mapping tests for mediawiki tables
    #***********
    def test_mediawiki_logging(self):
        row = self.mwSession.query(Logging).get(1)
        assert_true(row.log_user_text == 'Reedy')
    
    def test_mediawiki_user(self):
        row = self.mwSession.query(MediawikiUser).get(2)
        assert_true(row.user_name == 'Evan')
    
    def test_mediawiki_page(self):
        row = self.mwSession.query(Page).get(1)
        assert_true(row.page_title == 'Main_Page')
    
    def test_mediawiki_revision(self):
        row = self.mwSession.query(Revision).get(1)
        assert_true(row.rev_comment == 'Dan edit 1')
    
    #***********
    # Join tests
    #***********
    def test_cohort_members(self):
        user_ids = self.session\
            .query(WikiUser.mediawiki_userid)\
            .join(CohortWikiUser)\
            .filter(CohortWikiUser.cohort_id == 1)\
            .all()
        
        assert_true(len(user_ids) == 4, "Cohort 1 should have 4 wiki users in it")
