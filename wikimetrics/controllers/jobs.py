from flask import render_template, redirect, request
from wikimetrics.configurables import app


@app.route('/jobs/')
def jobs_index():
    """
    Renders a page with a list of jobs started by the currently logged in user.
    If the user is an admin, she has the option to see other users' jobs.
    """
    return 'jobs'
