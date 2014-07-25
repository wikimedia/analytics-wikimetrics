from unittest import TestCase
from sqlalchemy.exc import TimeoutError
from nose.tools import assert_equals, assert_true, raises

from tests.fixtures import mediawiki_project
from wikimetrics.configurables import db, parse_db_connection_string, queue
from wikimetrics.database import get_host_projects, get_host_projects_map
from wikimetrics.models import Page


class DatabaseSetupTest(TestCase):

    @raises(TimeoutError)
    def test_pool_size_can_be_exceeded(self):
        # The 11 in the following statement is 10 (default for
        # max_overflow) + 1. So this is the lowest value for which we
        # expect the connection to fail.
        pool_size = db.config['MEDIAWIKI_POOL_SIZE'] + 11
        self.sessions = [
            db.get_mw_session(mediawiki_project)
            for i in range(pool_size)
        ]
        [self.sessions[i].query(Page).all() for i in range(pool_size)]

    def test_pool_size_is_used(self):
        pool_size = db.config['MEDIAWIKI_POOL_SIZE']
        self.sessions = [
            db.get_mw_session(mediawiki_project)
            for i in range(pool_size)
        ]
        [self.sessions[i].query(Page).all() for i in range(pool_size)]
        assert_true(True)

    def tearDown(self):
        if hasattr(self, 'sessions'):
            sessions = getattr(self, 'sessions')
            for s in sessions:
                s.close()
