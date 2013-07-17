from flask import render_template, request, url_for, Response
from flask.ext.login import current_user
import celery
from ..configurables import app, db
from ..models import Cohort, Job, JobResponse, PersistentJob, MultiProjectMetricJob
from ..metrics import metric_classes
from ..utils import json_response, json_redirect, deduplicate
import json
from StringIO import StringIO
from csv import DictWriter


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
        parsed = json.loads(request.form['responses'])
        metric_jobs = []
        metric_names = []
        cohort_names = []
        for cohort_metric_dict in parsed:
            
            # get cohort
            cohort_dict = cohort_metric_dict['cohort']
            db_session = db.get_session()
            # TODO: filter by current_user
            cohort = db_session.query(Cohort).get(cohort_dict['id'])
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
            
            # construct and start JobResponse
            metric_job = MultiProjectMetricJob(cohort, metric)
            metric_jobs.append(metric_job)
            metric_names.append(metric.label)
            cohort_names.append(cohort.name)
        
        metric_names = deduplicate(metric_names)
        cohort_names = deduplicate(cohort_names)
        name = ', '.join(metric_names) + ' for ' + ', '.join(cohort_names)
        jr = JobResponse(metric_jobs, name=name)
        async_response = jr.task.delay()
        app.logger.info('starting job: %s', async_response.task_id)
        
        #return render_template('jobs.html')
        return json_redirect(url_for('jobs_index'))


@app.route('/jobs/list/')
def jobs_list():
    db_session = db.get_session()
    jobs = db_session.query(PersistentJob)\
        .filter_by(user_id=current_user.id)\
        .filter_by(show_in_ui=True).all()
    # update status for each job
    for job in jobs:
        job.update_status()
    
    # TODO fix json_response to deal with PersistentJob objects
    jobs_json = json_response(jobs=[job._asdict() for job in jobs])
    db_session.close()
    return jobs_json


@app.route('/jobs/status/<job_id>')
def job_status(job_id):
    db_session = db.get_session()
    db_job = db_session.query(PersistentJob).get(job_id)
    if db_job.status not in (celery.states.SUCCESS, celery.states.FAILURE):
        if db_job.result_key:
            # if we don't have the result key leave as is (PENDING)
            celery_task = Job.task.AsyncResult(db_job.result_key)
            db_job.status = celery_task.status
            db_session.add(db_job)
            db_session.commit()
    db_session.close()
    return json_response(status=db_job.status)


@app.route('/jobs/result/<job_id>.csv')
def job_result_csv(job_id):
    db_session = db.get_session()
    db_job = db_session.query(PersistentJob).get(job_id)
    celery_task = Job.task.AsyncResult(db_job.result_key)
    if celery_task.ready:
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
        return Response(csv_io.getvalue(), mimetype='text/csv')
    else:
        return json_response(status=celery_task.status)
        #return url_for('/jobs/list/')


@app.route('/jobs/result/<job_id>.json')
def job_result_json(job_id):
    db_session = db.get_session()
    db_job = db_session.query(PersistentJob).get(job_id)
    celery_task = Job.task.AsyncResult(db_job.result_key)
    if celery_task.ready:
        task_result = celery_task.get()
        return json_response(result=task_result)
    else:
        return json_response(status=celery_task.status)
        #return url_for('/jobs/list/')
