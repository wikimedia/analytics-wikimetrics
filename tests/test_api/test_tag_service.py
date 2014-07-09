from nose.tools import assert_true, assert_equal

from tests.fixtures import DatabaseTest
from wikimetrics.models import TagStore
from wikimetrics.api import TagService


class TagServiceTest(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self.tag_service = TagService()

    def test_get_all_tags(self):
        tag1 = TagStore(name="tag-1")
        tag2 = TagStore(name="tag-2")
        self.session.add(tag1)
        self.session.add(tag2)
        self.session.commit()
        tags = self.tag_service.get_all_tags(self.session)
        assert_true(len(tags), 2)
        assert_true(tags[0], "tag-1")
        assert_true(tags[1], "tag-2")

    def test_get_all_tags_empty(self):
        self.tag_service = TagService()
        tags = self.tag_service.get_all_tags(self.session)
        assert_equal(tags, [])
