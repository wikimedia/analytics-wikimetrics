from sqlalchemy.orm.exc import NoResultFound
from flask import render_template, request, url_for, Response
from flask.ext.login import current_user
from ..configurables import app, db
from ..models import Report, RunReport, PersistentReport
from ..models.report_nodes import Aggregation
from ..utils import json_response, json_error, json_redirect, thirty_days_ago
import json
from StringIO import StringIO
from csv import DictWriter


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
        jr = RunReport(desired_responses, user_id=current_user.id)
        jr.task.delay(jr)
        
        return json_redirect(url_for('reports_index'))


@app.route('/reports/list/')
def reports_list():
    db_session = db.get_session()
    reports = db_session.query(PersistentReport)\
        .filter(PersistentReport.user_id == current_user.id)\
        .filter(PersistentReport.created > thirty_days_ago())\
        .filter(PersistentReport.show_in_ui)\
        .all()
    # TODO: update status for all reports at all times (not just show_in_ui ones)
    # update status for each report
    for report in reports:
        report.update_status()
    
    # TODO fix json_response to deal with PersistentReport objects
    reports_json = json_response(reports=[report._asdict() for report in reports])
    db_session.close()
    return reports_json


def get_celery_task(result_key):
    """
    From a unique identifier, gets the celery task and database records associated.
    
    Parameters
        result_key  : The unique identifier found in the report database table
    
    Returns
        A tuple of the form (celery_task_object, database_report_object)
    """
    try:
        db_session = db.get_session()
        pj = db_session.query(PersistentReport)\
            .filter(PersistentReport.result_key == result_key)\
            .one()
        
        celery_task = Report.task.AsyncResult(pj.queue_result_key)
        db_session.close()
        return (celery_task, pj)
    except NoResultFound:
        return (None, None)


def get_celery_task_result(celery_task, db_report):
    # this indicates an old style result, the celery task result can be returned directly
    # TODO: delete this logic on October 1st, as all old results will have expired by then
    if db_report.result_key == db_report.queue_result_key:
        return celery_task.get()
    # otherwise, it's a new style result, the celery task is a dictionary
    else:
        return celery_task.get()[db_report.result_key]


@app.route('/reports/status/<result_key>')
def report_status(result_key):
    celery_task, pj = get_celery_task(result_key)
    return json_response(status=celery_task.status)


@app.route('/reports/result/<result_key>.csv')
def report_result_csv(result_key):
    celery_task, pj = get_celery_task(result_key)
    if not celery_task:
        return json_error('no task exists with id: {0}'.format(result_key))
    
    if celery_task.ready():
        task_result = get_celery_task_result(celery_task, pj)
        
        csv_io = StringIO()
        if task_result:
            columns = []
            
            if Aggregation.IND in task_result:
                columns = task_result[Aggregation.IND][0].values()[0].keys()
            elif Aggregation.SUM in task_result:
                columns = task_result[Aggregation.SUM].keys()
            elif Aggregation.AVG in task_result:
                columns = task_result[Aggregation.AVG].keys()
            elif Aggregation.STD in task_result:
                columns = task_result[Aggregation.STD].keys()
            
            # if task_result is not empty find header in first row
            fieldnames = ['user_id'] + columns
        else:
            fieldnames = ['user_id']
        writer = DictWriter(csv_io, fieldnames)
        
        # collect rows to output in CSV
        task_rows = []
        
        # Individual Results
        if Aggregation.IND in task_result:
            # fold user_id into dict so we can use DictWriter to escape things
            for user_id, row in task_result[Aggregation.IND][0].iteritems():
                task_row = row.copy()
                task_row['user_id'] = user_id
                task_rows.append(task_row)
        
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


        #========================================================

        parameters = json.loads(pj.parameters)

        # generate some empty rows to separate the result
        # from the parameters
        task_rows.append({})
        task_rows.append({})
        task_rows.append({ 'user_id': 'parameters' })

        for key,value in parameters.items():
            task_rows.append({ 'user_id': key , fieldnames[1]: value })

        task_rows.append({'user_id': 'metric/cohort name', fieldnames[1]: pj.name});
        
        writer.writeheader()
        writer.writerows(task_rows)
        return Response(csv_io.getvalue(), mimetype='text/csv')
    else:
        return json_response(status=celery_task.status)


@app.route('/reports/result/<result_key>.json')
def report_result_json(result_key):
    celery_task, pj = get_celery_task(result_key)
    if not celery_task:
        return json_error('no task exists with id: {0}'.format(result_key))
    
    if celery_task.ready():
        task_result = get_celery_task_result(celery_task, pj)
        
        return json_response(
            result=task_result,
            parameters=json.loads(pj.parameters),
        )
    else:
        return json_response(status=celery_task.status)


#@app.route('/reports/kill/<result_key>')
#def report_kill(result_key):
    #return 'not implemented'
    #db_session = db.get_session()
    #db_report = db_session.query(PersistentReport).get(result_key)
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
