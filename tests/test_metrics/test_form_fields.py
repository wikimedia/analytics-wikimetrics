from datetime import datetime, date
from unittest import TestCase
from nose.tools import assert_equals

from wikimetrics.metrics import NamespaceEdits
from wikimetrics.utils import to_datetime


class BetterDateTimeFieldTest(TestCase):
    def test_time_is_included(self):
        now = datetime.now()
        form = NamespaceEdits(start_date=now)

        assert_equals(form.start_date.data, now)

    def test_time_is_excluded(self):
        today = date.today()
        form = NamespaceEdits(start_date=today)

        assert_equals(form.start_date.data, to_datetime(today))
