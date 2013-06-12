from flask import render_template, redirect, request
from wikimetrics.web import app


@app.route('/cohorts/')
def cohorts_index():
    """
    This flask endpoint returns a list cohorts belonging to the currently logged in user
    If the user is an admin, she has the option of seeing other users' cohorts
    """
    return 'cohorts'
