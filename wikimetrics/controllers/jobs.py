from flask import render_template, redirect, request, jsonify
from flask.ext.login import current_user
from ..configurables import app, db
from ..models import PersistentJob
import logging
logger = logging.getLogger(__name__)


@app.route('/jobs/')
def jobs_index():
    """
    Renders a page with a list of jobs started by the currently logged in user.
    If the user is an admin, she has the option to see other users' jobs.
    """
    return render_template('jobs.html')


@app.route('/jobs/create/', methods=['GET', 'POST'])
def jobs_request():
    """
    Renders a page that facilitates kicking off a new job
    """
    if request.method == 'GET':
        return render_template('request.html')
    else:
        # TODO: validate the different metrics in request.form
        # TODO: create a JobResponse using responses=request.form['responses']
        return render_template('jobs.html')


@app.route('/jobs/list/')
def jobs_list():
    db_session = db.get_session()
    jobs = db_session.query(PersistentJob)\
        .filter_by(user_id=current_user.id).all()
    return jsonify(jobs=jobs)
