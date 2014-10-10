# coding=utf-8
from nose.tools import assert_true, assert_equal
from contextlib import contextmanager
from flask import appcontext_pushed, g
from tests.fixtures import WebTest
from wikimetrics.utils import parse_tag
from wikimetrics.api import CohortService
from wikimetrics.configurables import app
from wikimetrics.models import (
    TagStore, WikiUserStore
)


@contextmanager
def cohort_service_set(app, cohort_service):
    def handler(sender, **kwargs):
        g.cohort_service = cohort_service
    with appcontext_pushed.connected_to(handler, app):
        yield


class CohortsControllerUTF8Test(WebTest):
    def setUp(self):
        WebTest.setUp(self)
        self.cohort_service = CohortService()

    def test_add_new_tag_utf8(self):
        '''
        Tries to make sure inserting tags with utf-8 chars does not blow things up
        Please see encoding on 1st line of file
        '''
        tag = u"18Наталь"
        unparsed_tag = "  18Наталь   "
        parsed_tag = parse_tag(tag)
        response = self.app.post('/cohorts/{0}/tag/add/{1}'
                                 .format(self.cohort.id, unparsed_tag))
        assert_true(response.data.find('"tags":') >= 0)
        # TODO tag is coming like the following, that needs fixing
        # "tags": [
        #{
        #    "id": 14,
        #   "name": "18\u043d\u0430\u0442\u0430\u043b\u044c"
        #}
        self.session.commit()
        t = self.session.query(TagStore).filter(TagStore.name == parsed_tag).first()
        assert_true(t is not None)

    def test_invalid_wiki_user_utf8(self):
        '''
        Tests if usernames with utf-8 chars are rendered as expected in the
        list of invalid cohort users. For this test to work, 1st line of file
        should read '# coding=utf-8'.
        '''
        invalid = self.session.query(WikiUserStore).first()
        invalid.valid = False
        invalid.mediawiki_username = "ام محمود عبد المحس"
        invalid.reason_invalid = 'some reason'
        self.session.commit()
        with cohort_service_set(app, self.cohort_service):
            response = self.app.get('/cohorts/detail/invalid-users/{0}'.format(
                self.cohort.id
            ))
        assert_equal(response.status_code, 200)
        assert_true(response.data.find(invalid.mediawiki_username) >= 0)
