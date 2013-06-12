from flask import render_template, redirect, request
from wikimetrics.web import app


@app.route('/jobs/')
def jobs_index():
    return 'jobs'
