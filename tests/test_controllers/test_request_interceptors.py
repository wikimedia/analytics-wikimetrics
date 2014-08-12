from nose.tools import assert_true, assert_equals
from nose.plugins.attrib import attr
from sqlalchemy.event import listen

from tests.fixtures import WebTest
from wikimetrics.configurables import app, db


class RequestInterceptorsTest(WebTest):

    def test_n_requests_get_n_different_connections(self):
        """
        Note that /demo/get-session-and-leave-open opens not one but two sessions.
        We execute that code 10 times so regardless of the numbers of sessions opened,
        we should see just 1 distinct session, because all requests run in the same scope
        """
        global connections_opened
        connections_opened = 0
        requests_to_execute = 10

        def increment_counter(connection, branch):
            global connections_opened
            connections_opened = connections_opened + 1
        listen(db.wikimetrics_engine, 'engine_connect', increment_counter)

        for i in range(0, requests_to_execute + 1):
            self.client.get('/demo/get-session-and-leave-open')

        assert_equals(connections_opened, requests_to_execute + 1)
