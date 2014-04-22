import unittest
from nose.tools import assert_equal

from wikimetrics.models import WikiUserKey


class BasicTests(unittest.TestCase):
    
    def test_repr(self):
        wuk = WikiUserKey(123, 'wiki', 444)
        assert_equal(str(wuk), '123|wiki|444')
    
    def test_from_string(self):
        wuk = WikiUserKey.fromstr('123|wiki|444')
        assert_equal(wuk.user_id, '123')
        assert_equal(wuk.user_project, 'wiki')
        assert_equal(wuk.cohort_id, '444')
