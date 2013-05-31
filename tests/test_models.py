from nose.tools import *
from wikimetrics.database import init_db, Session
from wikimetrics.models import *

def setup():
    init_db()

def teardown():
    pass

# TODO: put these in a class and call setup / teardown more elegantly
setup()
#***********
# Mapping tests for our custom tables
#***********

def test_job():
    j = Job()
    session = Session()
    session.add(j)
    session.commit()
    
    get_j = session.query(Job).filter_by(id=j.id).first()
    assert_true(get_j.status == JobStatus.CREATED)
    
    session.delete(j)
    session.commit()
    
    get_j = session.query(Job).filter_by(id=j.id).first()
    assert_true(get_j is None)


def test_user():
    u = User(username='Dan')
    session = Session()
    session.add(u)
    session.commit()
    
    get_u = session.query(User).filter_by(id=u.id).first()
    assert_true(get_u.username == 'Dan')
    assert_true(get_u.role == UserRole.GUEST)
    
    session.delete(u)
    session.commit()
    
    get_u = session.query(User).filter_by(id=u.id).first()
    assert_true(get_u is None)


def test_wikiuser():
    wu = WikiUser(mediawiki_username='Milimetric')
    session = Session()
    session.add(wu)
    session.commit()
    
    get_wu = session.query(WikiUser).filter_by(id=wu.id).first()
    assert_true(get_wu.mediawiki_username == 'Milimetric')
    
    session.delete(wu)
    session.commit()

    get_wu = session.query(WikiUser).filter_by(id=wu.id).first()
    assert_true(get_wu is None)


def test_cohort():
    c = Cohort(name='Test')
    session = Session()
    session.add(c)
    session.commit()
    
    get_c = session.query(Cohort).filter_by(id=c.id).first()
    assert_true(get_c.name == 'Test')
    assert_true(get_c.public == False)
    
    session.delete(c)
    session.commit()
    
    get_c = session.query(Cohort).filter_by(id=c.id).first()
    assert_true(get_c is None)


def test_cohort_wikiuser():
    c = Cohort()
    wu = WikiUser()
    session = Session()
    session.add(c)
    session.add(wu)
    session.commit()
    
    cwu = CohortWikiUser(wiki_user_id=wu.id, cohort_id=c.id)
    session.add(cwu)
    session.commit()
    get_cwu = session.query(CohortWikiUser).filter_by(id=cwu.id).first()
    assert_true(get_cwu.wiki_user_id == wu.id)
    assert_true(get_cwu.cohort_id == c.id)
    
    session.delete(c)
    session.delete(wu)
    session.delete(cwu)
    session.commit()
    
    get_cwu = session.query(CohortWikiUser).filter_by(id=cwu.id).first()
    assert_true(get_cwu is None)

#***********
# Mapping tests for mediawiki tables
#***********
#def test__mediawiki_logging


teardown()
