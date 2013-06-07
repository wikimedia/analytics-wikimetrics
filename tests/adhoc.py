from tests.fixtures import DatabaseTest
from wikimetrics.database import Session
from wikimetrics.models import *
from wikimetrics.metrics import *

d = DatabaseTest()
d.setUp()

session = Session()
c = session.query(Cohort).get(1)
