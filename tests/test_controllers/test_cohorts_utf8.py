# -*- coding: utf-8 -*-
from nose.tools import assert_true
from tests.fixtures import WebTest
from wikimetrics.utils import parse_tag
from wikimetrics.models import (
    TagStore
)


class CohortsControllerUTF8Test(WebTest):
    def setUp(self):
        WebTest.setUp(self)

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

    def test_upload_cohort_with_utf8_description(self):
        '''
        Uploading cohorts with utf-8 characters in the description
        should not break cohort list request. Please, see encoding
        on the 1st line of this file.
        '''
        description = '18Наталь'
        response = self.app.post('/cohorts/upload', data=dict(
            name='utf8 description cohort',
            description=description,
            project='wiki',
            paste_ids_or_names='actual validation tested elsewhere',
            validate_as_user_ids='True',
        ))
        response = self.app.get('/cohorts/list?include_invalid=true',
                                follow_redirects=True)
        assert_true(description in response.data)
