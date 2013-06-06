from nose.tools import *
from wikimetrics.database import init_db, Session, MediawikiSession
from wikimetrics.metrics import RevertRateMetric

def setup():
    init_db()

def teardown():
    pass

# TODO: put these in a class and call setup / teardown more elegantly
setup()


def test_finds_reverts():
    assert_true(False)


def test_reports_zero_correctly():
    assert_true(False)


def test_reports_undefined_correctly():
    assert_true(False)


teardown()
