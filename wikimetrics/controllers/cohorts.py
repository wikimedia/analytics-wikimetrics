from flask import render_template, redirect, request, jsonify
from flask.ext.login import current_user
from ..configurables import app, db
from ..models import Cohort
import logging

logger = logging.getLogger(__name__)


@app.route('/cohorts/')
def cohorts_index():
    """
    Renders a page with a list cohorts belonging to the currently logged in user.
    If the user is an admin, she has the option of seeing other users' cohorts.
    """
    return 'cohorts'


@app.route('/cohorts/list/')
def cohorts_list():
    # TODO: add filtering by permission (this also needs db support)
    db_session = db.get_session()
    cohorts = db_session.query(Cohort)\
               .filter_by(enabled = True, public = True).all()
    return jsonify(cohorts = cohorts)

@app.route('/cohorts/detail/<int:id>')
def cohort_detail(id):
    db_session = db.get_session()
    cohort = db_session.query(Cohort)\
               .filter_by(enabled = True, public = True).get(id)
    return jsonify(cohort)
