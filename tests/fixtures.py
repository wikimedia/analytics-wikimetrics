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
        session = MediawikiSession()
        session.add(MediawikiUser(user_id=2,user_name='12.222.101.118'))
        session.add(Logging(log_id=1,log_user_text='Reedy'))
        session.add(Page(page_id=1,page_title='Main_Page'))
        session.add(Revision(rev_id=10,rev_user_text='Platonides'))
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
