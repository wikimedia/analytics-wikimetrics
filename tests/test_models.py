from nose.tools import *
from wikimetrics.database import init_db, Session, MediawikiSession
from wikimetrics.models import *
from fixtures import *


class TestMappings(DatabaseTest):
    #***********
    # Mapping tests for our custom tables
    #***********

    def test_job(self):
        j = Job()
        session = Session()
        session.add(j)
        session.commit()
        
        get_j = session.query(Job).get(j.id)
        assert_true(get_j.status == JobStatus.CREATED)
        
        session.delete(j)
        session.commit()
        
        get_j = session.query(Job).get(j.id)
        assert_true(get_j is None)


    def test_user(self):
        u = User(username='Dan')
        session = Session()
        session.add(u)
        session.commit()
        
        get_u = session.query(User).get(u.id)
        assert_true(get_u.username == 'Dan')
        assert_true(get_u.role == UserRole.GUEST)
        
        session.delete(u)
        session.commit()
        
        get_u = session.query(User).get(u.id)
        assert_true(get_u is None)


    def test_wikiuser(self):
        wu = WikiUser(mediawiki_username='Milimetric')
        session = Session()
        session.add(wu)
        session.commit()
        
        get_wu = session.query(WikiUser).get(wu.id)
        assert_true(get_wu.mediawiki_username == 'Milimetric')
        
        session.delete(wu)
        session.commit()

        get_wu = session.query(WikiUser).get(wu.id)
        assert_true(get_wu is None)


    def test_cohort(self):
        c = Cohort(name='Test')
        session = Session()
        session.add(c)
        session.commit()
        
        get_c = session.query(Cohort).get(c.id)
        assert_true(get_c.name == 'Test')
        assert_true(get_c.public == False)
        
        session.delete(c)
        session.commit()
        
        get_c = session.query(Cohort).get(c.id)
        assert_true(get_c is None)


    def test_cohort_wikiuser(self):
        c = Cohort()
        wu = WikiUser()
        session = Session()
        session.add(c)
        session.add(wu)
        session.commit()
        
        cwu = CohortWikiUser(wiki_user_id=wu.id, cohort_id=c.id)
        session.add(cwu)
        session.commit()
        get_cwu = session.query(CohortWikiUser).get(cwu.id)
        assert_true(get_cwu.wiki_user_id == wu.id)
        assert_true(get_cwu.cohort_id == c.id)
        
        session.delete(c)
        session.delete(wu)
        session.delete(cwu)
        session.commit()
        
        get_cwu = session.query(CohortWikiUser).get(cwu.id)
        assert_true(get_cwu is None)

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
