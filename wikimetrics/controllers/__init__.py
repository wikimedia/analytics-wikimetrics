"""
The routing strategy of wikimetrics is as follows:
    
    /api/*  routes are used via AJAX and by any third party clients.  These return JSON.
    /*      routes are normal routes.

This package is organized by the logical units called controllers.  Each controller can have
both types of routes.
At a future time, / could serve the index and routing could move client-side.
"""
from home import *
from authentication import *
from metrics import *
from cohorts import *
from reports import *
from demo import *

# ignore flake8 because of F403 violation
# flake8: noqa
