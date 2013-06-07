import unittest
from nose.tools import *

from queue import celery
from wikimetrics.database import init_db, Session, MediawikiSession
from wikimetrics.models import *

__all__ = [
    'DatabaseTest',
    'QueueTest',
]

class DatabaseTest(unittest.TestCase):
    def runTest(self):
        pass
    
    def setUp(self):
        init_db()
        
        # create records for mediawiki tests
        mwSession = MediawikiSession()
        mwSession.add(MediawikiUser(user_id=2,user_name='12.222.101.118'))
        mwSession.add(Logging(log_id=1,log_user_text='Reedy'))
        mwSession.add(Page(page_id=1,page_title='Main_Page'))
        mwSession.add(Revision(rev_id=10,rev_user_text='Platonides'))
        mwSession.commit()
        
        # create basic test records for non-mediawiki tests
        session = Session()
        
        job = Job()
        user = User(username='Dan')
        
        # create a test cohort
        dan = WikiUser(
            mediawiki_username='Dan',
            mediawiki_userid=1,
            project='enwiki',
        )
        evan = WikiUser(
            mediawiki_username='Evan',
            mediawiki_userid=2,
            project='enwiki',
        )
        andrew = WikiUser(
            mediawiki_username='Andrew',
            mediawiki_userid=3,
            project='enwiki',
        )
        diederik = WikiUser(
            mediawiki_username='Diederik',
            mediawiki_userid=4,
            project='enwiki',
        )
        test = Cohort(
            name='test',
        )
        session.add_all([job, user, dan, evan, andrew, diederik, test])
        session.commit()
        
        dan_in_test = CohortWikiUser(
            wiki_user_id=dan.id,
            cohort_id=test.id
        )
        evan_in_test = CohortWikiUser(
            wiki_user_id=evan.id,
            cohort_id=test.id
        )
        andrew_in_test = CohortWikiUser(
            wiki_user_id=andrew.id,
            cohort_id=test.id
        )
        diederik_in_test = CohortWikiUser(
            wiki_user_id=diederik.id,
            cohort_id=test.id
        )
        session.add_all([
            dan_in_test,
            evan_in_test,
            andrew_in_test,
            diederik_in_test
        ])
        session.commit()
    
    def tearDown(self):
        
        # delete records
        mwSession = MediawikiSession()
        mwSession.query(MediawikiUser).delete()
        mwSession.query(Logging).delete()
        mwSession.query(Page).delete()
        mwSession.query(Revision).delete()
        mwSession.commit()
        
        session = Session()
        session.query(CohortWikiUser).delete()
        session.query(WikiUser).delete()
        session.query(Cohort).delete()
        session.query(User).delete()
        session.query(Job).delete()
        session.commit()


class QueueTest(unittest.TestCase):
    
    def setUp(self):
        celery.start()
    
    def tearDown(self):
        pass
