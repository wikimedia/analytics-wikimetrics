from nose.tools import *
from wikimetrics.database import init_db, Session
from wikimetrics.models import *

def setup():
    init_db()

def teardown():
    pass

setup()

def test_job_maps_correctly_to_db():
    j = Job(status=JobStatus.CREATED)
    session = Session()
    session.add(j)
    session.commit()
    
    get_j = session.query(Job).filter_by(id=j.id).first()
    assert_true(get_j.status == JobStatus.CREATED)
    
    del j
    session.commit()


def test_user_maps_correctly_to_db():
    u = User(username='Dan')
    session = Session()
    session.add(u)
    session.commit()
    
    get_u = session.query(User).filter_by(id=u.id).first()
    assert_true(get_u.username == 'Dan')
    assert_true(get_u.role == UserRole.GUEST)
    
    del u
    session.commit()


def test_wikiuser_maps_correctly_to_db():
    wu = WikiUser(mediawiki_username='Milimetric')
    session = Session()
    session.add(wu)
    session.commit()
    
    get_wu = session.query(WikiUser).filter_by(id=wu.id).first()
    assert_true(get_wu.mediawiki_username == 'Milimetric')
    
    del wu
    session.commit()


def test_cohort_maps_correctly_to_db():
    c = Cohort(name='Test')
    session = Session()
    session.add(c)
    session.commit()
    
    get_c = session.query(Cohort).filter_by(id=c.id).first()
    assert_true(get_c.name == 'Test')
    
    del c
    session.commit()


def test_cohort_wikiuser_maps_correctly_to_db():
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
    
    del c
    del wu
    del cwu
    session.commit()


teardown()
