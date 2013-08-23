import json
import csv
from flask import url_for, flash, render_template, redirect, request
from flask.ext.login import current_user
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from ..utils import json_response, json_error, json_redirect, deduplicate_by_key
from ..configurables import app, db
from ..models import (
    Cohort, CohortUser, CohortUserRole,
    User, WikiUser, CohortWikiUser, MediawikiUser
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
    db_session = db.get_session()
    cohorts = db_session.query(Cohort.id, Cohort.name, Cohort.description)\
        .join(CohortUser)\
        .join(User)\
        .filter(User.id == current_user.id)\
        .filter(CohortUser.role.in_([CohortUserRole.OWNER, CohortUserRole.VIEWER]))\
        .filter(Cohort.enabled)\
        .all()
    
    db_session.close()
    return json_response(cohorts=[{
        'id': c.id,
        'name': c.name,
        'description': c.description,
    } for c in cohorts])


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
    if str(name_or_id).isdigit():
        cohort = get_cohort_by_id(int(name_or_id))
    else:
        cohort = get_cohort_by_name(name_or_id)
    
    if cohort:
        limit = None if full_detail == 'true' else 3
        cohort_with_wikiusers = populate_cohort_wikiusers(cohort, limit)
        return json_response(cohort_with_wikiusers)
    
    return '{}', 404


def get_cohort_query():
    allowed_roles = [CohortUserRole.OWNER, CohortUserRole.VIEWER]
    db_session = db.get_session()
    return (
        db_session.query(Cohort)
                  .join(CohortUser)
                  .join(User)
                  .filter(User.id == current_user.id)
                  .filter(CohortUser.role.in_(allowed_roles))
                  .filter(Cohort.enabled),
        db_session
    )


def get_cohort_by_id(id):
    try:
        query, db_session = get_cohort_query()
        cohort = query.filter(Cohort.id == id).one()
        db_session.close()
        return cohort
    except (MultipleResultsFound, NoResultFound):
        return None


def get_cohort_by_name(name):
    try:
        query, db_session = get_cohort_query()
        cohort = query.filter(Cohort.name == name).one()
        db_session.close()
        return cohort
    except (MultipleResultsFound, NoResultFound):
        return None


def populate_cohort_wikiusers(cohort, limit):
    db_session = db.get_session()
    wikiusers = db_session.query(WikiUser)\
        .join(CohortWikiUser)\
        .filter(CohortWikiUser.cohort_id == cohort.id)\
        .limit(limit)\
        .all()
    
    db_session.close()
    cohort_dict = cohort._asdict()
    cohort_dict['wikiusers'] = [wu._asdict() for wu in wikiusers]
    return cohort_dict


@app.route('/cohorts/upload', methods=['GET', 'POST'])
def cohort_upload():
    """ View for uploading and validating a new cohort via CSV """
    if request.method == 'GET':
        return render_template(
            'csv_upload.html',
            projects=json.dumps(db.project_host_map.keys()),
        )

    elif request.method == 'POST':
        try:
            csv_file = request.files['csv']
            name = request.form['name']
            project = request.form['project']
            description = request.form['description']
            if not csv_file or not name or len(name) is 0:
                flash('The form was invalid, please'
                      'select a file and name the cohort.', 'error')
                return redirect(url_for('cohort_upload'))
            
            if get_cohort_by_name(name):
                flash('That Cohort name is already taken.', 'warning')
                return redirect(url_for('cohort_upload'))
            
            unparsed = csv.reader(normalize_newlines(csv_file.stream))
            unvalidated = parse_records(unparsed, project)
            (valid, invalid) = validate_records(unvalidated)
            
            return render_template(
                'csv_upload_review.html',
                valid=valid,
                invalid=invalid,
                valid_json=to_safe_json(valid),
                invalid_json=to_safe_json(invalid),
                name=name,
                project=project,
                description=description,
                projects=json.dumps(db.project_host_map.keys()),
            )
        except Exception, e:
            app.logger.exception(str(e))
            flash(
                'The file you uploaded was not in a valid format, could not be validated,'
                'or the project you specified is not configured on this instance of '
                'Wiki Metrics.', 'error'
            )
            return redirect(url_for('cohort_upload'))


@app.route('/cohorts/create', methods=['POST'])
def cohort_upload_finish():
    try:
        name = request.form.get('name')
        # re-validate the name
        if get_cohort_by_name(name):
            raise Exception('Cohort name {0} is already used'.format(name))
        
        project = request.form.get('project')
        description = request.form.get('description')
        users_json = request.form.get('users')
        users = json.loads(users_json)
        
        # NOTE: If we don't re-validate here, the user can change the cohort client-side
        # This will produce weird results but we sort of don't care.
        
        # Save the cohort
        valid = users
        for valid_user in valid:
            # SQLAlchemy complains about the names unless we encode them
            valid_user['username'] = valid_user['username'].encode('utf8')
        
        if not project:
            if all([user['project'] == users[0]['project'] for user in users]):
                project = users[0]['project']
        
        if not project:
            return json_error('If all the users do not belong to the same project, '
                              'your cohort needs a default project.')
        
        create_cohort(name, description, project, valid)
        return json_redirect(url_for('cohorts_index'))
    
    except Exception, e:
        app.logger.exception(str(e))
        return json_error(
            'There was a problem finishing the upload.  The cohort was not saved.'
        )


def create_cohort(name, description, project, valid_users):
    db_session = db.get_session()
    cohort = Cohort(
        name=name,
        default_project=project,
        description=description,
        enabled=True,
    )
    db_session.add(cohort)
    db_session.commit()
    
    cohort_owner = CohortUser(
        cohort_id=cohort.id,
        user_id=current_user.id,
        role=CohortUserRole.OWNER,
    )
    db_session.add(cohort_owner)
    
    wikiusers = []
    for valid_user in valid_users:
        wikiuser = WikiUser(
            mediawiki_userid=valid_user['user_id'],
            mediawiki_username=valid_user['username'],
        )
        wikiusers.append(wikiuser)
    db_session.add_all(wikiusers)
    db_session.commit()
    
    cohort_wikiusers = []
    for wikiuser in wikiusers:
        cohort_wikiuser = CohortWikiUser(
            cohort_id=cohort.id,
            wiki_user_id=wikiuser.id,
        )
        cohort_wikiusers.append(cohort_wikiuser)
    db_session.add_all(cohort_wikiusers)
    db_session.commit()
    
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


def normalize_newlines(stream):
    for line in stream:
        if '\r' in line:
            for tok in line.split('\r'):
                yield tok
        else:
            yield line


def to_safe_json(s):
    return json.dumps(s).replace("'", "\\'").replace('"', '\\"')


def parse_records(records, default_project):
    # NOTE: the reason for the crazy -1 and comma joins
    # is that some users can have commas in their name
    # NOTE: This makes it impossible to add fields to the csv in the future,
    # so maybe require the project to be the first field and the username to be the last
    # or maybe change to a tsv format
    parsed = []
    for r in records:
        if r:
            if len(r) > 1:
                username = ",".join([str(p) for p in r[:-1]])
                project = r[-1].decode('utf8') or default_project
            else:
                username = r[0]
                project = default_project
            
            parsed.append({
                'raw_username': parse_username(username, decode=False),
                'username': parse_username(username),
                'project': project,
            })
    return parsed


def parse_username(username, decode=True):
    """
    parses uncapitalized, whitespace-padded, and weird-charactered mediawiki
    user names into ones that have a chance of being found in the database
    """
    username = str(username)
    username = username.decode('utf8')
    stripped = username.strip()
    if not decode:
        stripped = stripped.encode('utf8')
    # Capitalize the username according to the Mediawiki standard
    # NOTE: unfortunately .title() or .capitalize() don't work
    # because 'miliMetric'.capitalize() == 'Milimetric'
    return stripped[0].upper() + stripped[1:]


def normalize_project(project):
    project = project.strip().lower()
    if project in db.project_host_map:
        return project
    else:
        # try adding wiki to end
        new_proj = project + 'wiki'
        if new_proj not in db.project_host_map:
            return None
        else:
            return new_proj


def get_wikiuser_by_name(username, project):
    db_session = db.get_mw_session(project)
    try:
        wikiuser = db_session.query(MediawikiUser)\
            .filter(MediawikiUser.user_name == username)\
            .one()
        db_session.close()
        return wikiuser
    except (MultipleResultsFound, NoResultFound):
        db_session.close()
        return None


def get_wikiuser_by_id(id, project):
    db_session = db.get_mw_session(project)
    try:
        wikiuser = db_session.query(MediawikiUser)\
            .filter(MediawikiUser.user_id == id)\
            .one()
        db_session.close()
        return wikiuser
    except (MultipleResultsFound, NoResultFound):
        db_session.close()
        return None


def normalize_user(user_str, project):
    wikiuser = get_wikiuser_by_name(user_str, project)
    if wikiuser is not None:
        return (wikiuser.user_id, wikiuser.user_name)
    
    if not user_str.isdigit():
        return None
    
    wikiuser = get_wikiuser_by_id(user_str, project)
    if wikiuser is not None:
        return (wikiuser.user_id, wikiuser.user_name)
    
    return None


def project_name_for_link(project):
    if project.endswith('wiki'):
        return project[:len(project) - 4]
    return project


def link_to_user_page(username, project):
    project = project_name_for_link(project)
    return 'https://{0}.wikipedia.org/wiki/User:{1}'.format(project, username)


def validate_records(records):
    valid = []
    invalid = []
    for record in records:
        normalized_project = normalize_project(record['project'])
        link_project = normalized_project or record['project'] or 'invalid'
        record['user_str'] = record['username']
        record['link'] = link_to_user_page(record['username'], link_project)
        if normalized_project is None:
            record['reason_invalid'] = 'invalid project: %s' % record['project']
            invalid.append(record)
            continue
        normalized_user = normalize_user(record['raw_username'], normalized_project)
        # make a link to the potential user page even if user doesn't exist
        # this gives a chance to see any misspelling etc.
        if normalized_user is None:
            app.logger.info(
                'invalid user: {0} in project {1}'
                .format(record['raw_username'], normalized_project)
            )
            record['reason_invalid'] = 'invalid user_name / user_id: {0}'.format(
                record['user_str']
            )
            invalid.append(record)
            continue
        # set the normalized values and append to valid
        record['project'] = normalized_project
        record['user_id'], record['username'] = normalized_user
        valid.append(record)
    
    valid = deduplicate_by_key(valid, lambda record: record['username'])
    return (valid, invalid)
