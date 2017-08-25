import json
import celery
import traceback
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
from null_report import NullReport
from validate_report import ValidateReport
from metric_report import MetricReport
from wikimetrics.api import ReportService, CohortService
from wikimetrics.utils import stringify
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

    def __init__(self,
                 parameters,
                 user_id=0,
                 recurrent_parent_id=None,
                 created=None,
                 persistent_id=None):
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
            created             : if set, represents the date of a recurrent run.
                                  This need not be the timestamp when the
                                  recurrent run has been created -- for example
                                  when backfilling. Hence, this does not fully
                                  match the semantics of the word 'created'.
                                  But since neither start nor end date have a
                                  separate column in the report table in the
                                  database, the covered period for backfilled
                                  recurring reports would be hard to identify
                                  when only looking at the raw database
                                  tables. To overcome this issue, we abuse the
                                  created date here.

        Raises:
            KeyError if required parameters are missing
        """
        # get cohort
        cohort_service = CohortService()
        cohort_dict = parameters['cohort']
        session = db.get_session()
        cohort = cohort_service.get(session, user_id, by_id=cohort_dict['id'])

        parameters['cohort']['size'] = cohort.size

        # construct metric
        metric_dict = parameters['metric']
        metric = metric_classes[metric_dict['name']](**metric_dict)

        # if this is a recurrent run, don't show it in the UI
        if recurrent_parent_id is not None:
            self.show_in_ui = False

        public = parameters.get('public', False)
        recurrent = parameters.get('recurrent', False)

        super(RunReport, self).__init__(
            name=parameters['name'],
            user_id=user_id,
            parameters=parameters,
            public=public,
            recurrent=recurrent,
            recurrent_parent_id=recurrent_parent_id,
            created=created,
            store=True,
            persistent_id=persistent_id
        )

        self.recurrent_parent_id = recurrent_parent_id
        self.public = public

        validate_report = ValidateReport(
            metric, cohort, recurrent_parent_id is None, user_id=user_id
        )
        if validate_report.valid():
            if recurrent and recurrent_parent_id is None:
                # Valid parent recurrent report
                # We do not add children that compute data as parent recurrent
                # reports just help the scheduler orchestrate child runs.
                # However, we employ a NullReport to allow coalescing even
                # when there was no recurrent run yet.
                self.children = [NullReport()]
            else:
                # Valid, but not a parent recurring report, so we add the child
                # node that does the real computation
                self.children = [AggregateReport(
                    metric, cohort, metric_dict, parameters=parameters,
                    user_id=user_id
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

        rs = ReportService()
        rs.write_report_to_file(self, results, db.get_session())

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
                    created=day,  # See constructor of RunReport
                )
                reports_created += 1
            except Exception, e:
                # don't need to roll back session because it's just a query
                task_logger.error('Problem creating child report: {}, params: {}'.format(
                    traceback.format_exc(e),
                    stringify(parameters)
                ))
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

        # if a report is pending by this point, it means that it should be re-tried
        session.query(ReportStore) \
            .filter(ReportStore.recurrent_parent_id == report.id) \
            .filter(ReportStore.created >= search_from) \
            .filter(ReportStore.status == celery.states.PENDING) \
            .delete()

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

    @classmethod
    def rerun(cls, report):
        """
        Create an instance of RunReport from an existing ReportStore, and run it.
        The persistent_id is passed to the constructor so that the existing
        ReportStore is used instead of creating a new one.
        """
        rerun = RunReport(
            json.loads(report.parameters),
            user_id=report.user_id,
            persistent_id=report.id
        )
        rerun.set_status(celery.states.PENDING)
        return rerun.task.delay(rerun)
