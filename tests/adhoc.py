from tests.fixtures import DatabaseTest
from wikimetrics.database import db
from wikimetrics.models import *
from wikimetrics.metrics import *

d = DatabaseTest()
d.setUp()

session = db.get_session()
c = session.query(Cohort).get(1)

mwSession = db.get_mw_session('enwiki')
