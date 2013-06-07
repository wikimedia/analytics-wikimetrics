from nose.tools import *
from unittest import TestCase

from queue import celery
from wikimetrics.database import init_db, Session, MediawikiSession
from wikimetrics.models import *

__all__ = [
    'DatabaseTest',
]

class DatabaseTest(TestCase):
    
    def setUp(self):
        init_db()
        
        # create records for mediawiki tests
        mwSession = MediawikiSession()
        mwSession.add(MediawikiUser(user_id=2,user_name='12.222.101.118'))
        mwSession.add(Logging(log_id=1,log_user_text='Reedy'))
        mwSession.add(Page(page_id=1,page_title='Main_Page'))
        mwSession.add(Revision(rev_id=10,rev_user_text='Platonides'))
        mwSession.commit()
        
        # create a test cohort
        session = Session()
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
        session.add_all([dan, evan, andrew, test])
        session.commit()
        
        dan_in_test = CohortWikiUser(
            wiki_user_id=dan.id(),
            cohort_id=test.id()
        )
        evan_in_test = CohortWikiUser(
            wiki_user_id=evan.id(),
            cohort_id=test.id()
        )
        andrew_in_test = CohortWikiUser(
            wiki_user_id=andrew.id(),
            cohort_id=test.id()
        )
        diederik_in_test = CohortWikiUser(
            wiki_user_id=diederik.id(),
            cohort_id=test.id()
        )
        session.add_all([
            dan_in_test,
            evan_in_test,
            andrew_in_test,
            diederik_in_test
        ])
        session.commit()
    
    def tearDown(self):
        
        # delete records for mediawiki tests
        session = MediawikiSession()
        session.query(MediawikiUser).delete()
        session.query(Logging).delete()
        session.query(Page).delete()
        session.query(Revision).delete()
        session.commit()


class QueueTest(TestCase):
    
    def setUp(self):
        celery.start()
    
    def tearDown(self):
        pass
