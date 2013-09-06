import datetime
import decimal
from nose.tools import assert_true, assert_equals
from unittest import TestCase
from wikimetrics.utils import (
    stringify,
)
from wikimetrics.metrics import NamespaceEdits


class UtilsTest(TestCase):
    
    def test_better_encoder_date(self):
        string = stringify(date_not_date_time=datetime.date(2013, 06, 01))
        assert_true(string.find('"date_not_date_time"') >= 0)
    
    def test_better_encoder_decimal(self):
        string = stringify(deci=decimal.Decimal(6.01))
        assert_true(string.find('"deci"') >= 0)
    
    def test_better_encoder_default(self):
        string = stringify(normal='hello world')
        assert_true(string.find('"normal"') >= 0)
