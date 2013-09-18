# ignore flake8 because of F403 violation
# flake8: noqa


#####################################
# Run this script with
# ipython -i scripts/debug.py
#####################################

from sqlalchemy import func
from wikimetrics.models import Revision, Page, User, MediawikiUser
#from wikimetrics.models.mediawiki import
from tests.fixtures import DatabaseTest, DatabaseWithSurvivorCohortTest
from tests.test_metrics.test_survivors import *
from wikimetrics.metrics import Survivors
from wikimetrics.configurables import db
from pprint import pprint
import calendar

# Mediawiki database
d = db.get_mw_session("enwiki")

# Wikimetrics database
m = db.get_session()

s = SurvivorsTest()
s.setUp()

# %load_ext autoreload
# %autoreload 2
