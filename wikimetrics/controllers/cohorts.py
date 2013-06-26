from flask import render_template, redirect, request, jsonify
from flask.ext.login import current_user
from ..configurables import app, db
from ..models import Cohort, CohortUser, CohortUserRole, User, WikiUser, CohortWikiUser
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
    cohorts = db_session.query(Cohort.id,Cohort.name,Cohort.description)\
               .join(CohortUser)\
               .join(User)\
               .filter(User.id==current_user.id)\
               .filter(CohortUser.role.in_([CohortUserRole.OWNER,CohortUserRole.VIEWER]))\
               .filter(Cohort.enabled==True)\
               .all()
    return jsonify(cohorts = cohorts)


@app.route('/cohorts/detail/<int:id>')
def cohort_detail(id):
    """
    Returns a JSON object of the form:
    {id: 2, name: 'Berlin Beekeeping Society', description: '', wikiusers: [
        {mediawiki_username: 'Andrea', mediawiki_userid: 5, project: 'dewiki'},
        {mediawiki_username: 'Dennis', mediawiki_userid: 6, project: 'dewiki'},
        {mediawiki_username: 'Florian', mediawiki_userid: 7, project: 'dewiki'},
        {mediawiki_username: 'Gabriele', mediawiki_userid: 8, project: 'dewiki'},
    ]}
    """
    db_session = db.get_session()
    cohort = db_session.query(Cohort)\
               .join(CohortUser)\
               .join(User)\
               .filter(CohortUser.role.in_([CohortUserRole.OWNER,CohortUserRole.VIEWER]))\
               .filter(Cohort.enabled == True)\
               .filter(Cohort.id == id)\
               .one()
    wikiusers = db_session.query(WikiUser)\
               .join(CohortWikiUser)\
               .filter(CohortWikiUser.cohort_id == cohort.id)\
               .all()
    cohort_dict = cohort._asdict()
    cohort_dict['wikiusers'] = [wu._asdict() for wu in wikiusers]
    return jsonify(cohort_dict)
