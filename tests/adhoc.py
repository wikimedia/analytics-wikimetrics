from tests.fixtures import DatabaseTest
from wikimetrics.database import get_session, get_mw_session
from wikimetrics.models import *
from wikimetrics.metrics import *

d = DatabaseTest()
d.setUp()

session = get_session()
c = session.query(Cohort).get(1)

mwSession = get_mw_session('enwiki')
