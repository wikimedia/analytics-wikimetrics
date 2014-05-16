import json
from csv import DictWriter
from StringIO import StringIO
from sqlalchemy.orm.exc import NoResultFound
from flask import render_template, request, redirect, url_for, Response, abort, g
from flask.ext.login import current_user
from sqlalchemy.exc import SQLAlchemyError
from wikimetrics.configurables import app, db
from wikimetrics.models import (
    Report, RunReport, Aggregation,
    ReportStore, WikiUserStore, WikiUserKey,
)
from wikimetrics.metrics import TimeseriesChoices
from wikimetrics.utils import (
    json_response, json_error, json_redirect, thirty_days_ago, stringify
)
from wikimetrics.exceptions import UnauthorizedReportAccessError
from wikimetrics.api import PublicReportFileManager


@app.before_request
def setup_filemanager():
    if request.endpoint is not None:
        if 'report' in request.endpoint:
            file_manager = getattr(g, 'file_manager', None)
            if file_manager is None:
                g.file_manager = PublicReportFileManager(
                    app.logger,
                    app.absolute_path_to_app_root)


@app.route('/reports/unset-public/<int:report_id>', methods=['POST'])
def unset_public_report(report_id):
    """
    Deletes the specified report from disk, and sets the public flag to False.
    """
    # call would throw an exception if  report cannot be made private
    ReportStore.make_report_private(report_id, current_user.id, g.file_manager)
    return json_response(message='Update successful')


@app.route('/reports/set-public/<int:report_id>', methods=['POST'])
def set_public_report(report_id):
    """
    Client facing method with pretty url to set/uset one report as public
    """

    # in order to move code to the PersistenReport class need to fetch report
    # data here
    db_session = db.get_session()
    try:
        result_key = db_session.query(ReportStore.result_key)\
            .filter(ReportStore.id == report_id)\
            .one()[0]
    finally:
        db_session.close()

    data = report_result_json(result_key).data

    # call would throw an exception if report cannot be made public
    ReportStore.make_report_public(
        report_id, current_user.id, g.file_manager, data
    )

    return json_response(message='Update successful')


@app.route('/reports/')
def reports_index():
    """
    Renders a page with a list of reports started by the currently logged in user.
    If the user is an admin, she has the option to see other users' reports.
    """
    return render_template('reports.html')


@app.route('/reports/create/', methods=['GET', 'POST'])
def reports_request():
    """
    Renders a page that facilitates kicking off a new report
    """

    if request.method == 'GET':
        return render_template('report.html')
    else:
        desired_responses = json.loads(request.form['responses'])
        recurrent = json.loads(request.form.get('recurrent', 'false'))

        for parameters in desired_responses:
            parameters['recurrent'] = recurrent
            # NOTE: this is not a mistake.  Currently recurrent => public on creation
            parameters['public'] = recurrent
            jr = RunReport(parameters, user_id=current_user.id)
            jr.task.delay(jr)

        return json_redirect(url_for('reports_index'))


@app.route('/reports/list/')
def reports_list():
    db_session = db.get_session()
    try:
        reports = db_session.query(ReportStore)\
            .filter(ReportStore.user_id == current_user.id)\
            .filter(ReportStore.created > thirty_days_ago())\
            .filter(ReportStore.show_in_ui)\
            .all()
        # TODO: update status for all reports at all times (not just show_in_ui ones)
        # update status for each report
        for report in reports:
            report.update_status()

        # TODO fix json_response to deal with ReportStore objects
        reports_json = json_response(reports=[report._asdict() for report in reports])
    finally:
        db_session.close()
    return reports_json


def get_celery_task(result_key):
    """
    From a unique identifier, gets the celery task and database records associated.

    Parameters
        result_key  : The unique identifier found in the report database table
                        This parameter is required and should not be None

    Returns
        A tuple of the form (celery_task_object, database_report_object)
    """
    if not result_key:
        return (None, None)

    try:
        db_session = db.get_session()
        try:
            pj = db_session.query(ReportStore)\
                .filter(ReportStore.result_key == result_key)\
                .one()

            celery_task = Report.task.AsyncResult(pj.queue_result_key)
        finally:
            db_session.close()
        return (celery_task, pj)
    except NoResultFound:
        return (None, None)


@app.route('/reports/status/<result_key>')
def report_status(result_key):
    celery_task, pj = get_celery_task(result_key)
    return json_response(status=celery_task.status)


@app.route('/reports/result/<result_key>.csv')
def report_result_csv(result_key):
    celery_task, pj = get_celery_task(result_key)
    if not celery_task:
        return json_error('no task exists with id: {0}'.format(result_key))

    if celery_task.ready() and celery_task.successful():
        result = celery_task.get()
        task_result = pj.get_result_safely(result)
        p = pj.pretty_parameters()

        if 'Metric_timeseries' in p and p['Metric_timeseries'] != TimeseriesChoices.NONE:
            csv_io = get_timeseries_csv(task_result, pj, p)
        else:
            csv_io = get_simple_csv(task_result, pj, p)

        res = Response(csv_io.getvalue(), mimetype='text/csv')
        res.headers['Content-Disposition'] =\
            'attachment; filename={0}.csv'.format(pj.name)
        return res
    else:
        return json_response(status=celery_task.status)


def get_user_name(session, wiki_user_key):
    """
    Parameters
        session         : a session to the wikimetrics database to search with
        wiki_user_key   : an instance of WikiUserKey to search for a WikiUser with
    """
    return session.query(WikiUserStore.mediawiki_username)\
        .filter(WikiUserStore.mediawiki_userid == wiki_user_key.user_id)\
        .filter(WikiUserStore.project == wiki_user_key.user_project)\
        .filter(WikiUserStore.validating_cohort == wiki_user_key.cohort_id)\
        .one()[0]


def get_timeseries_csv(task_result, pj, parameters):
    """
    Parameters
        task_result : the result dictionary from Celery
        pj          : a pointer to the permanent job
        parameters  : a dictionary of pj.parameters

    Returns
        A StringIO instance representing timeseries CSV
    """
    csv_io = StringIO()
    if task_result:
        columns = []

        if Aggregation.IND in task_result:
            columns = task_result[Aggregation.IND].values()[0].values()[0].keys()
        elif Aggregation.SUM in task_result:
            columns = task_result[Aggregation.SUM].values()[0].keys()
        elif Aggregation.AVG in task_result:
            columns = task_result[Aggregation.AVG].values()[0].keys()
        elif Aggregation.STD in task_result:
            columns = task_result[Aggregation.STD].values()[0].keys()

        # if task_result is not empty find header in first row
        fieldnames = ['user_id', 'user_name', 'submetric'] + sorted(columns)
    else:
        fieldnames = ['user_id', 'user_name', 'submetric']
    writer = DictWriter(csv_io, fieldnames)

    # collect rows to output in CSV
    task_rows = []

    try:
        session = db.get_session()
        # Individual Results
        if Aggregation.IND in task_result:
            # fold user_id into dict so we can use DictWriter to escape things
            for wiki_user_key_str, row in task_result[Aggregation.IND].iteritems():
                wiki_user_key = WikiUserKey.fromstr(wiki_user_key_str)
                user_id = wiki_user_key.user_id
                user_name = get_user_name(session, wiki_user_key)
                for subrow in row.keys():
                    task_row = row[subrow].copy()
                    task_row['user_id'] = user_id
                    task_row['user_name'] = user_name
                    task_row['submetric'] = subrow
                    task_rows.append(task_row)
    finally:
        session.close()

    # Aggregate Results
    if Aggregation.SUM in task_result:
        row = task_result[Aggregation.SUM]
        for subrow in row.keys():
            task_row = row[subrow].copy()
            task_row['user_id'] = Aggregation.SUM
            task_row['submetric'] = subrow
            task_rows.append(task_row)

    if Aggregation.AVG in task_result:
        row = task_result[Aggregation.AVG]
        for subrow in row.keys():
            task_row = row[subrow].copy()
            task_row['user_id'] = Aggregation.AVG
            task_row['submetric'] = subrow
            task_rows.append(task_row)

    if Aggregation.STD in task_result:
        row = task_result[Aggregation.STD]
        for subrow in row.keys():
            task_row = row[subrow].copy()
            task_row['user_id'] = Aggregation.STD
            task_row['submetric'] = subrow
            task_rows.append(task_row)

    # generate some empty rows to separate the result
    # from the parameters
    task_rows.append({})
    task_rows.append({})
    task_rows.append({'user_id': 'parameters'})

    for key, value in sorted(parameters.items()):
        task_rows.append({'user_id': key , fieldnames[1]: value})

    writer.writeheader()
    writer.writerows(task_rows)
    return csv_io


def get_simple_csv(task_result, pj, parameters):
    """
    Parameters
        task_result : the result dictionary from Celery
        pj          : a pointer to the permanent job
        parameters  : a dictionary of pj.parameters

    Returns
        A StringIO instance representing simple CSV
    """

    csv_io = StringIO()
    if task_result:
        columns = []

        if Aggregation.IND in task_result:
            columns = task_result[Aggregation.IND].values()[0].keys()
        elif Aggregation.SUM in task_result:
            columns = task_result[Aggregation.SUM].keys()
        elif Aggregation.AVG in task_result:
            columns = task_result[Aggregation.AVG].keys()
        elif Aggregation.STD in task_result:
            columns = task_result[Aggregation.STD].keys()

        # if task_result is not empty find header in first row
        fieldnames = ['user_id', 'user_name'] + columns
    else:
        fieldnames = ['user_id', 'user_name']
    writer = DictWriter(csv_io, fieldnames)

    # collect rows to output in CSV
    task_rows = []

    try:
        session = db.get_session()
        # Individual Results
        if Aggregation.IND in task_result:
            # fold user_id into dict so we can use DictWriter to escape things
            for wiki_user_key_str, row in task_result[Aggregation.IND].iteritems():
                wiki_user_key = WikiUserKey.fromstr(wiki_user_key_str)
                user_id = wiki_user_key.user_id
                user_name = get_user_name(session, wiki_user_key)
                task_row = row.copy()
                task_row['user_id'] = user_id
                task_row['user_name'] = user_name
                task_rows.append(task_row)
    finally:
        session.close()

    # Aggregate Results
    if Aggregation.SUM in task_result:
        task_row = task_result[Aggregation.SUM].copy()
        task_row['user_id'] = Aggregation.SUM
        task_rows.append(task_row)

    if Aggregation.AVG in task_result:
        task_row = task_result[Aggregation.AVG].copy()
        task_row['user_id'] = Aggregation.AVG
        task_rows.append(task_row)

    if Aggregation.STD in task_result:
        task_row = task_result[Aggregation.STD].copy()
        task_row['user_id'] = Aggregation.STD
        task_rows.append(task_row)

    # generate some empty rows to separate the result
    # from the parameters
    task_rows.append({})
    task_rows.append({})
    task_rows.append({'user_id': 'parameters'})

    for key, value in sorted(parameters.items()):
        task_rows.append({'user_id': key , fieldnames[1]: value})

    writer.writeheader()
    writer.writerows(task_rows)
    return csv_io


@app.route('/reports/result/<result_key>.json')
def report_result_json(result_key):
    celery_task, pj = get_celery_task(result_key)
    if not celery_task:
        return json_error('no task exists with id: {0}'.format(result_key))

    if celery_task.ready() and celery_task.successful():
        result = celery_task.get()
        json_result = pj.get_json_result(result)

        return json_response(json_result)
    else:
        return json_response(status=celery_task.status)


#@app.route('/reports/kill/<result_key>')
#def report_kill(result_key):
    #return 'not implemented'
    #db_session = db.get_session()
    #db_report = db_session.query(ReportStore).get(result_key)
    #if not db_report:
        #return json_error('no task exists with id: {0}'.format(result_key))
    #celery_task = Report.task.AsyncResult(db_report.result_key)
    #app.logger.debug('revoking task: %s', celery_task.id)
    #from celery.task.control import revoke
    #celery_task.revoke()
    # TODO figure out how to terminate tasks. this throws an error
    # which I believe is related to https://github.com/celery/celery/issues/1153
    # and which is fixed by a patch.  however, I can't get things running
    # with development version
    #revoke(celery_task.id, terminate=True)
    #return json_response(status=celery_task.status)

########   Internal functions not available via HTTP ################################
