from flask import render_template, redirect, request
from wikimetrics.web import app


@app.route('/jobs/')
def jobs_index():
    """
    This flask endpoint returns a list jobs started by the currently logged in user
    If the user is an admin, she has the option to see other users' jobs
    """
    return 'jobs'
