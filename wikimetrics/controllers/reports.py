from flask import render_template, request, url_for, Response
from flask.ext.login import current_user
import celery
from celery.task.control import revoke
from ..configurables import app, db
from ..models import (
    Cohort, CohortUser, CohortUserRole, Report,
    RunReport, PersistentReport, MultiProjectMetricReport
)
from ..metrics import metric_classes
from ..utils import json_response, json_error, json_redirect, deduplicate, thirty_days_ago
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
        return render_template('request.html')
    else:
        parsed = json.loads(request.form['responses'])
        metric_reports = []
        metric_names = []
        cohort_names = []
        for cohort_metric_dict in parsed:
            
            # get cohort
            cohort_dict = cohort_metric_dict['cohort']
            db_session = db.get_session()
            cohort = db_session.query(Cohort)\
                .filter(CohortUser.role.in_([CohortUserRole.OWNER, CohortUserRole.VIEWER]))\
                .filter(Cohort.enabled)\
                .filter_by(id=cohort_dict['id'])\
                .one()
            db_session.close()
            
            # construct metric
            metric_dict = cohort_metric_dict['metric']
            class_name = metric_dict.pop('name')
            metric_class = metric_classes[class_name]
            metric = metric_class(**metric_dict)
            metric.validate()
            
            # debug output
            #app.logger.debug('cohort_metric_dict: %s', cohort_metric_dict)
            #app.logger.debug('cohort: %s', cohort)
            #app.logger.debug('metric: %s', metric)
            
            # construct and start RunReport
            metric_report = MultiProjectMetricReport(
                cohort,
                metric,
                name=cohort_metric_dict['name'],
            )
            metric_reports.append(metric_report)
            metric_names.append(metric.label)
            cohort_names.append(cohort.name)
        
        metric_names = deduplicate(metric_names)
        cohort_names = deduplicate(cohort_names)
        name = ', '.join(metric_names) + ' for ' + ', '.join(cohort_names)
        jr = RunReport(metric_reports, name=name)
        async_response = jr.task.delay()
        app.logger.info(
            'starting report with celery_id: %s, PersistentReport.id: %d',
            async_response.task_id, jr.persistent_id
        )
        
        #return render_template('reports.html')
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


@app.route('/reports/status/<report_id>')
def report_status(report_id):
    db_session = db.get_session()
    db_report = db_session.query(PersistentReport).get(report_id)
    if db_report.status not in (celery.states.SUCCESS, celery.states.FAILURE):
        if db_report.result_key:
            # if we don't have the result key leave as is (PENDING)
            celery_task = Report.task.AsyncResult(db_report.result_key)
            db_report.status = celery_task.status
            db_session.add(db_report)
            db_session.commit()
    db_session.close()
    return json_response(status=db_report.status)


@app.route('/reports/result/<report_id>.csv')
def report_result_csv(report_id):
    response = ''
    db_session = db.get_session()
    db_report = db_session.query(PersistentReport).get(report_id)
    if not db_report:
        return json_error('no task exists with id: {0}'.format(report_id))
    celery_task = Report.task.AsyncResult(db_report.result_key)
    if celery_task.ready():
        task_result = celery_task.get()
        
        csv_io = StringIO()
        if task_result:
            # if task_result is not empty find header in first row
            fieldnames = ['user_id'] + sorted(task_result.values()[0].keys())
        else:
            fieldnames = ['user_id']
        writer = DictWriter(csv_io, fieldnames)
        
        task_rows = []
        # fold user_id into dict so we can use DictWriter to escape things
        for user_id, row in task_result.iteritems():
            row['user_id'] = user_id
            task_rows.append(row)
        writer.writeheader()
        writer.writerows(task_rows)
        app.logger.debug('celery task is ready! returning actual result:\n%s', csv_io.getvalue())
        response = Response(csv_io.getvalue(), mimetype='text/csv')
    else:
        response = json_response(status=celery_task.status)
    
    db_session.close()
    return response


@app.route('/reports/result/<report_id>.json')
def report_result_json(report_id):
    response = ''
    db_session = db.get_session()
    db_report = db_session.query(PersistentReport).get(report_id)
    if not db_report:
        return json_error('no task exists with id: {0}'.format(report_id))
    celery_task = Report.task.AsyncResult(db_report.result_key)
    if celery_task.ready():
        task_result = celery_task.get()
        response = json_response(
            result=task_result,
            parameters=json.loads(db_report.parameters),
        )
    else:
        response = json_response(status=celery_task.status)
    
    db_session.close()
    return response


@app.route('/reports/kill/<report_id>')
def report_kill(report_id):
    db_session = db.get_session()
    db_report = db_session.query(PersistentReport).get(report_id)
    if not db_report:
        return json_error('no task exists with id: {0}'.format(report_id))
    celery_task = Report.task.AsyncResult(db_report.result_key)
    app.logger.debug('revoking task: %s', celery_task.id)
    #celery_task.revoke()
    # TODO figure out how to terminate tasks. this throws an error
    # which I believe is related to https://github.com/celery/celery/issues/1153
    # and which is fixed by a patch.  however, I can't get things running
    # with development version
    #revoke(celery_task.id, terminate=True)
    return json_response(status=celery_task.status)
