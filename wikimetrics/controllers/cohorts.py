from flask import render_template, redirect, request
from wikimetrics.web import app

@app.route('/cohorts/')
def cohorts_index():
    return 'cohorts'
