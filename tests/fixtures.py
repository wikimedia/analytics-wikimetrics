import unittest
from nose.tools import *

__all__ = [
    'DatabaseTest',
    'QueueTest',
    'QueueDatabaseTest',
    'WebTest',
]


from wikimetrics.database import init_db, Session, get_mw_session
from wikimetrics.models import *


class DatabaseTest(unittest.TestCase):
    
    def runTest(self):
        pass
    
    @classmethod
    def setUpClass(cls):
        init_db()
        pass
    
    def setUp(self):
        
        # create basic test records for non-mediawiki tests
        self.session = Session()
        
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
        self.session.add_all([job, user, dan, evan, andrew, diederik, test])
        self.session.commit()
        
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
        self.session.add_all([
            dan_in_test,
            evan_in_test,
            andrew_in_test,
            diederik_in_test
        ])
        self.session.commit()
        
        # create records for enwiki tests
        self.mwSession = get_mw_session('enwiki')
        self.mwSession.add(MediawikiUser(user_id=1, user_name='Dan'))
        self.mwSession.add(MediawikiUser(user_id=2, user_name='Evan'))
        self.mwSession.add(MediawikiUser(user_id=3, user_name='Andrew'))
        self.mwSession.add(Logging(log_id=1, log_user_text='Reedy'))
        self.mwSession.add(Page(page_id=1, page_namespace=0, page_title='Main_Page'))
        # Dan edits
        self.mwSession.add(Revision(rev_id=1, rev_page=1, rev_user=1, rev_comment='Dan edit 1'))
        self.mwSession.add(Revision(rev_id=2, rev_page=1, rev_user=1, rev_comment='Dan edit 2'))
        # Evan edits
        self.mwSession.add(Revision(rev_id=3, rev_page=1, rev_user=2, rev_comment='Evan edit 1'))
        self.mwSession.add(Revision(rev_id=4, rev_page=1, rev_user=2, rev_comment='Evan edit 2'))
        self.mwSession.add(Revision(rev_id=5, rev_page=1, rev_user=2, rev_comment='Evan edit 3'))
        self.mwSession.commit()
    
    def tearDown(self):
        
        # delete records
        self.mwSession.query(MediawikiUser).delete()
        self.mwSession.query(Logging).delete()
        self.mwSession.query(Page).delete()
        self.mwSession.query(Revision).delete()
        self.mwSession.commit()
        
        self.session = Session()
        self.session.query(CohortWikiUser).delete()
        self.session.query(WikiUser).delete()
        self.session.query(Cohort).delete()
        self.session.query(User).delete()
        self.session.query(Job).delete()
        self.session.commit()


from subprocess import Popen
from os import devnull
from signal import SIGINT
from queue import celery_is_alive
from time import sleep


class QueueTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # TODO configure celery verbosity
        celery_out = open(devnull, "w")
        celery_cmd = ['/usr/bin/python', 'queue.py', 'worker', '-l', 'debug']
        cls.celery_proc = Popen(celery_cmd, stdout=celery_out, stderr=celery_out)

        # wait until celery broker / worker is up
        while(not celery_is_alive()):
            sleep(0.5)
    
    @classmethod
    def tearDownClass(cls):
        cls.celery_proc.send_signal(SIGINT)


class QueueDatabaseTest(QueueTest, DatabaseTest):

    def setUp(self):
        QueueTest.setUp(self)
        DatabaseTest.setUp(self)

    def tearDown(self):
        QueueTest.tearDown(self)
        DatabaseTest.tearDown(self)


from wikimetrics import web


class WebTest(unittest.TestCase):
    
    def setUp(self):
        self.app = web.app.test_client()
    
    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)
    
    def logout(self):
        return self.app.get('/logout', follow_redirects=True)
