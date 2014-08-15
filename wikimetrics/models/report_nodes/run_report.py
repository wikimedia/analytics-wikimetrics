import json
import celery
from celery.utils.log import get_task_logger
from copy import deepcopy
from sqlalchemy.orm.exc import NoResultFound
from datetime import timedelta

from wikimetrics.configurables import db
from wikimetrics.models.storage.cohort import CohortStore
from wikimetrics.models.storage.report import ReportStore
from wikimetrics.metrics import metric_classes
from wikimetrics.utils import (
    diff_datewise, timestamps_to_now, strip_time, to_datetime, thirty_days_ago,
)
from report import ReportNode
from aggregate_report import AggregateReport
from validate_report import ValidateReport
from metric_report import MetricReport
from wikimetrics.api import write_report_task, CohortService
from wikimetrics.utils import BetterEncoder
from wikimetrics.schedules import recurring_reports

__all__ = ['RunReport']
task_logger = get_task_logger(__name__)


class RunReport(ReportNode):
    """
    Represents a batch of cohort-metric reports created by the
    user during a single reports/create/ workflow.  This is also
    intended to be the unit of work which could be easily re-run.
    """

    show_in_ui = True

    def __init__(self, parameters, user_id=0, recurrent_parent_id=None, created=None):
        """
        Parameters:
            parameters          : dictionary containing the following required keys:
                name            : the name of the report
                cohort          : dictionary defining the cohort, has keys:
                    id          : the id of the cohort
                metric          : dictionary defining the metric, has keys:
                    name        : the name of the python class to instantiate
                recurrent       : whether to rerun this daily
                public          : whether to expose results publicly
            user_id             : the user wishing to run this report
            recurrent_parent_id : the parent ReportStore.id for a recurrent run
            created             : if set, represents the date of a recurrent run

        Raises:
            KeyError if required parameters are missing
        """
        # get cohort
        cohort_service = CohortService()
        cohort_dict = parameters['cohort']
        session = db.get_session()
        try:
            cohort = cohort_service.get(session, user_id, by_id=cohort_dict['id'])
        finally:
            session.close()

        parameters['cohort']['size'] = cohort.size

        # construct metric
        metric_dict = parameters['metric']
        metric = metric_classes[metric_dict['name']](**metric_dict)

        # if this is a recurrent run, don't show it in the UI
        if recurrent_parent_id is not None:
            self.show_in_ui = False

        public = parameters.get('public', False)

        super(RunReport, self).__init__(
            name=parameters['name'],
            user_id=user_id,
            parameters=parameters,
            public=public,
            recurrent=parameters.get('recurrent', False),
            recurrent_parent_id=recurrent_parent_id,
            created=created,
        )

        self.recurrent_parent_id = recurrent_parent_id
        self.public = public

        validate_report = ValidateReport(
            metric, cohort, recurrent_parent_id is None, user_id=user_id
        )
        if validate_report.valid():
            self.children = [AggregateReport(
                metric, cohort, metric_dict, parameters=parameters, user_id=user_id
            )]
        else:
            self.children = [validate_report]

    def finish(self, aggregated_results):
        result = self.report_result(aggregated_results[0])
        return result

    def post_process(self, results):
        """
         If the report is public and this task went well,
         it will create a file on disk asynchronously.

         Results are of this form:

         Parameters:
            results : data to write to disk, in this form:
                {'5cab8d55-da19-436f-b675-1d2a3fca3481':
                    {'Sum': {'pages_created': Decimal('0.0000')}}
                }
        """

        if self.public is False:
            return

        try:
            session = db.get_session()
            db_report = session.query(ReportStore).get(self.persistent_id)
        finally:
            session.close()

        data = db_report.get_json_result(results)

        # code below schedules an async task on celery to write the file
        if self.recurrent_parent_id is not None:
            write_report_task.delay(self.recurrent_parent_id, self.created, data)
        else:
            # report is public and does not have a recurrent_parent_id, it's
            # the parent report, call the first run of the report
            self._run_child_report()

    def _run_child_report(self):
        '''
        Returns the scheduler we use for recurrent reports, right
        now the secduler for recurrent reports is a task on another python module
        what makes testing difficult.
        Ading this level of indirection makes testing easier
        '''
        recurring_reports(self.persistent_id)

    def __repr__(self):
        return '<RunReport("{0}")>'.format(self.persistent_id)

    # TODO, this method belongs on a different class and it should not be a class method
    @classmethod
    def create_reports_for_missed_days(cls, report, session, no_more_than=365):
        """
        Find which runs of a recurrent report were missed and create one report for each
        of those runs.  For reports on timeseries metrics, this method will set the
        end_date to midnight, today.  For non-timeseries metrics, it will set the
        start_date to yesterday and end_date to today.

        Parameters:
            report          : the parent recurrent report
            session         : a database session to the wikimetrics database
            no_more_than    : do not create more than this many reports, defaults to 365

        Returns:
            An array of RunReport instances that each represent a missed run of the
            parent report passed in.  The current day's run is considered a missed run for
            simplicity.  However, truly missed runs may be flagged so maintainers
            can troubleshoot reports that may have systemic problems.
        """
        # get the days the report needs to be run for
        days_missed = cls.days_missed(report, session)

        reports_created = 0
        for day in days_missed:
            try:
                # get the report parameters
                parameters = json.loads(report.parameters)

                # update the date parameters for this run of the metric
                metric = parameters['metric']
                # TODO: all metrics need to have an 'end_date' parameter in order to run
                # recurrently.  This should be at least less hardcoded if not more elegant
                metric['start_date'] = day - timedelta(days=1)
                metric['end_date'] = day

                # without this, reports would recur infinitely
                parameters['recurrent'] = False
                parameters['public'] = report.public

                new_run = cls(
                    parameters,
                    user_id=report.user_id,
                    recurrent_parent_id=report.id,
                    created=day,
                )
                reports_created += 1
            except Exception, e:
                task_logger.error('Problem creating child report: {}'.format(e))
                continue

            yield new_run

            if reports_created >= no_more_than:
                break

    # TODO, this method belongs on a different class and it should not be a class method
    @classmethod
    def days_missed(cls, report, session):
        """
        Examine the past runs of a recurring report
        Find any missed runs, including today's run.  Raise an exception if there
        are more runs than expected.

        Parameters:
            report  : the recurring report to examine
            session : session to the database

        Returns:
            An array of datetimes representing the days when the report did not run
        """
        search_from = strip_time(report.created)

        completed_days = [pr[0] for pr in session.query(ReportStore.created)
                          .filter(ReportStore.recurrent_parent_id == report.id)
                          .filter(ReportStore.created >= search_from)
                          .filter(ReportStore.status != celery.states.FAILURE)
                          .all()]
        expected_days = timestamps_to_now(search_from, timedelta(days=1))
        missed_days, unexpected_days = diff_datewise(expected_days, completed_days)

        if len(unexpected_days) > 0:
            task_logger.warn('Problem with recurrent report id {}'.format(report.id))
            task_logger.warn('Completed runs: {}'.format(sorted(completed_days)))
            task_logger.warn('Unexpected runs: {}'.format(sorted(unexpected_days)))
            raise Exception('More reports ran than were supposed to')

        return sorted(missed_days)
