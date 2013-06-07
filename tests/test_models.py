from nose.tools import *
from wikimetrics.database import init_db, Session, MediawikiSession
from wikimetrics.models import *
from fixtures import *


class TestMappings(DatabaseTest):
    #***********
    # Mapping tests for our custom tables
    #***********

    def test_job(self):
        session = Session()
        j = session.query(Job).get(1)
        assert_true(j.status == JobStatus.CREATED)


    def test_user(self):
        session = Session()
        u = session.query(User).get(1)
        assert_true(u.username == 'Dan')
        assert_true(u.role == UserRole.GUEST)


    def test_wikiuser(self):
        session = Session()
        wu = session.query(WikiUser).get(1)
        assert_true(wu.mediawiki_username == 'Dan')


    def test_cohort(self):
        session = Session()
        c = session.query(Cohort).get(1)
        assert_true(c.name == 'test')
        assert_true(c.public == False)


    def test_cohort_wikiuser(self):
        session = Session()
        cwu = session.query(CohortWikiUser).get(1)
        assert_true(cwu.wiki_user_id == 1)
        assert_true(cwu.cohort_id == 1)


    #***********
    # Mapping tests for mediawiki tables
    #***********
    def test_mediawiki_logging(self):
        session = MediawikiSession()
        row = session.query(Logging).get(1)
        assert_true(row.log_user_text == 'Reedy')


    def test_mediawiki_user(self):
        session = MediawikiSession()
        row = session.query(MediawikiUser).get(2)
        assert_true(row.user_name == '12.222.101.118')


    def test_mediawiki_page(self):
        session = MediawikiSession()
        row = session.query(Page).get(1)
        assert_true(row.page_title == 'Main_Page')


    def test_mediawiki_revision(self):
        session = MediawikiSession()
        row = session.query(Revision).get(10)
        assert_true(row.rev_user_text == 'Platonides')
    
    
    #***********
    # Join tests
    #***********
    def test_cohort_members(self):
        session = Session()
        user_ids = session\
            .query(WikiUser.mediawiki_userid)\
            .join(CohortWikiUser)\
            .filter(CohortWikiUser.cohort_id == 1)\
            .all()
        
        assert_true(len(user_ids) == 4, "Cohort 1 should have 4 wiki users in it")
