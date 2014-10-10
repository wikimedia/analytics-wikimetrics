import unittest
from nose.tools import assert_equals
from wtforms import Form, IntegerField, StringField

from wikimetrics.forms import BetterDateTimeField
from wikimetrics.forms.validators import NotGreater
from wikimetrics.utils import thirty_days_ago, today


class WTFormsValidatorsTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_not_greater(self):
        class DateForm(Form):
            start_date = BetterDateTimeField(validators=[NotGreater('end_date')])
            end_date = BetterDateTimeField()

        class NumberForm(Form):
            start = IntegerField(validators=[NotGreater('end')])
            end = IntegerField()

        class MixedForm(Form):
            start = IntegerField(validators=[NotGreater('end')])
            end = StringField()

        form = DateForm(start_date=thirty_days_ago(), end_date=today())
        assert_equals(form.validate(), True)

        form = DateForm(start_date=today(), end_date=thirty_days_ago())
        assert_equals(form.validate(), False)

        form = NumberForm(start=1, end=2)
        assert_equals(form.validate(), True)

        form = NumberForm(start=3, end=2)
        assert_equals(form.validate(), False)

        form = NumberForm(start=3, end=3)
        assert_equals(form.validate(), True)

        form = MixedForm(start=3, end='abc')
        assert_equals(form.validate(), False)
