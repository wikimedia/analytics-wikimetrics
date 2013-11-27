import json
from flask import url_for, flash, render_template, redirect, request
from flask.ext.login import current_user
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.sql.expression import or_
from ..utils import (
    json_response, json_error, json_redirect, deduplicate_by_key, Unauthorized
)
from ..configurables import app, db
from ..controllers.forms import CohortUpload
from ..models import (
    Cohort, CohortUser, CohortUserRole,
    User, WikiUser, CohortWikiUser, MediawikiUser,
    ValidateCohort
)


@app.route('/cohorts/')
def cohorts_index():
    """
    Renders a page with a list cohorts belonging to the currently logged in user.
    If the user is an admin, she has the option of seeing other users' cohorts.
    """
    return render_template('cohorts.html')


@app.route('/cohorts/list/')
def cohorts_list():
    include_invalid = request.args.get('include_invalid', 'false')
    db_session = db.get_session()
    try:
        cohorts = db_session.query(Cohort.id, Cohort.name, Cohort.description)\
            .join(CohortUser)\
            .join(User)\
            .filter(User.id == current_user.id)\
            .filter(CohortUser.role.in_(CohortUserRole.SAFE_ROLES))\
            .filter(Cohort.enabled)\
            .filter(or_(
                Cohort.validated,
                (include_invalid == 'true')
            ))\
            .all()
    finally:
        db_session.close()
    
    return json_response(cohorts=[{
        'id': c.id,
        'name': c.name,
        'description': c.description,
    } for c in cohorts])


@app.route('/cohorts/detail/invalid-users/<int:cohort_id>')
def cohort_invalid_detail(cohort_id):
    session = db.get_session()
    try:
        cohort = Cohort.get_safely(session, current_user.id, by_id=cohort_id)
        wikiusers = session.query(WikiUser.mediawiki_username, WikiUser.reason_invalid)\
            .filter(WikiUser.validating_cohort == cohort.id) \
            .filter(WikiUser.valid.in_([False, None])) \
            .all()
        return json_response(invalid_wikiusers=[wu._asdict() for wu in wikiusers])
    except:
        return json_error('Error fetching invalid users for {0}'.format(cohort_id))
    finally:
        session.close()


@app.route('/cohorts/detail/<string:name_or_id>')
def cohort_detail(name_or_id):
    """
    Returns a JSON object of the form:
    {id: 2, name: 'Berlin Beekeeping Society', description: '', wikiusers: [
        {mediawiki_username: 'Andrea', mediawiki_userid: 5, project: 'dewiki'},
        {mediawiki_username: 'Dennis', mediawiki_userid: 6, project: 'dewiki'},
        {mediawiki_username: 'Florian', mediawiki_userid: 7, project: 'dewiki'},
        {mediawiki_username: 'Gabriele', mediawiki_userid: 8, project: 'dewiki'},
    ]}
    """
    full_detail = request.args.get('full_detail', 0)
    
    cohort = None
    db_session = db.get_session()
    try:
        if str(name_or_id).isdigit():
            cohort = Cohort.get_safely(db_session, current_user.id, by_id=int(name_or_id))
        else:
            cohort = Cohort.get_safely(db_session, current_user.id, by_name=name_or_id)
    except Unauthorized:
        return 'You are not allowed to access this Cohort', 401
    except NoResultFound:
        return 'Could not find this Cohort', 404
    finally:
        db_session.close()
    
    limit = 200 if full_detail == 'true' else 3
    cohort_with_wikiusers = populate_cohort_wikiusers(cohort, limit)
    cohort_with_status = populate_cohort_validation_status(cohort_with_wikiusers)
    return json_response(cohort_with_status)


def populate_cohort_wikiusers(cohort, limit):
    """
    Fetches up to <limit> WikiUser records belonging to <cohort>
    """
    session = db.get_session()
    try:
        wikiusers = cohort.filter_wikiuser_query(
            session.query(WikiUser)
        ).limit(limit).all()
    finally:
        session.close()
    cohort_dict = cohort._asdict()
    cohort_dict['wikiusers'] = [wu._asdict() for wu in wikiusers]
    return cohort_dict


def populate_cohort_validation_status(cohort_dict):
    task_key = cohort_dict['validation_queue_key']
    if not task_key:
        cohort_dict['validation_status'] = 'UNKNOWN'
        cohort_dict['validated_count'] = len(cohort_dict['wikiusers'])
        cohort_dict['total_count'] = len(cohort_dict['wikiusers'])
        cohort_dict['valid_count'] = cohort_dict['total_count']
        cohort_dict['invalid_count'] = 0
        return cohort_dict
    
    validation_task = ValidateCohort.task.AsyncResult(task_key)
    cohort_dict['validation_status'] = validation_task.status
    
    session = db.get_session()
    try:
        cohort_dict['invalid_count'] = session.query(func.count(WikiUser)) \
            .filter(WikiUser.validating_cohort == cohort_dict['id']) \
            .filter(WikiUser.valid.in_([False])) \
            .one()[0]
        cohort_dict['valid_count'] = session.query(func.count(WikiUser)) \
            .filter(WikiUser.validating_cohort == cohort_dict['id']) \
            .filter(WikiUser.valid) \
            .one()[0]
        cohort_dict['validated_count'] = cohort_dict['valid_count'] \
            + cohort_dict['invalid_count']
        cohort_dict['total_count'] = session.query(func.count(WikiUser)) \
            .filter(WikiUser.validating_cohort == cohort_dict['id']) \
            .one()[0]
    finally:
        session.close()
    return cohort_dict


@app.route('/cohorts/upload', methods=['GET', 'POST'])
def cohort_upload():
    """ View for uploading and validating a new cohort via CSV """
    form = CohortUpload()
    
    if request.method == 'POST':
        form = CohortUpload.from_request(request)
        try:
            if not form.validate():
                flash('Please fix validation problems.', 'warning')
            elif get_cohort_by_name(form.name.data):
                flash('That Cohort name is already taken.', 'warning')
            else:
                form.parse_records()
                vc = ValidateCohort.from_upload(form, current_user.id)
                vc.task.delay(vc)
                return redirect('{0}#{1}'.format(
                    url_for('cohorts_index'),
                    vc.cohort_id
                ))
        except Exception, e:
            app.logger.exception(str(e))
            flash('Server error while processing your upload', 'error')
    
    return render_template(
        'csv_upload.html',
        projects=json.dumps(sorted(db.project_host_map.keys())),
        form=form,
    )


def get_cohort_by_name(name):
    """
    Gets a cohort by name, without checking access or worrying about duplicates
    """
    try:
        db_session = db.get_session()
        return db_session.query(Cohort).filter(Cohort.name == name).first()
    finally:
        db_session.close()


@app.route('/cohorts/validate/name')
def validate_cohort_name_allowed():
    name = request.args.get('name')
    available = get_cohort_by_name(name) is None
    return json.dumps(available)


@app.route('/cohorts/validate/project')
def validate_cohort_project_allowed():
    project = request.args.get('project')
    valid = project in db.project_host_map
    return json.dumps(valid)


@app.route('/cohorts/validate/<int:cohort_id>', methods=['POST'])
def validate_cohort(cohort_id):
    name = None
    session = db.get_session()
    try:
        cohort = Cohort.get_safely(session, current_user.id, by_id=cohort_id)
        name = cohort.name
        vc = ValidateCohort(cohort)
        vc.task.delay(vc)
        return json_response(message='Validating cohort "{0}"'.format(name))
    except Unauthorized:
        return json_error('You are not allowed to access this cohort')
    except NoResultFound:
        return json_error('This cohort does not exist')
    finally:
        session.close()


@app.route('/cohorts/delete/<int:cohort_id>', methods=['POST'])
def delete_cohort(cohort_id):
    """
    Deletes a cohort and all its wikiusers if it belongs to only current_user
    Removes the relationship between current_user and this cohort if it belongs
    to more than just current_user
    """
    session = db.get_session()
    try:
        result = session.query(CohortUser) \
            .filter(CohortUser.cohort_id == cohort_id) \
            .filter(CohortUser.user_id == current_user.id) \
            .delete()
        session.commit()
        if result > 0:
            return json_redirect(url_for('cohorts_index'))
        else:
            return json_error('This Cohort can not be deleted')
    finally:
        session.close()
