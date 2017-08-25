from celery.utils.log import get_task_logger
from datetime import timedelta

from wikimetrics.enums import Aggregation
from wikimetrics.metrics import metric_classes
from report import ReportNode
from aggregate_report import AggregateReport
from validate_program_metrics_report import ValidateProgramMetricsReport
from sum_aggregate_by_user_report import SumAggregateByUserReport
from wikimetrics.api import ReportService, CohortService
from wikimetrics.configurables import db

__all__ = ['RunProgramMetricsReport']
task_logger = get_task_logger(__name__)
cohort_service = CohortService()


class RunProgramMetricsReport(ReportNode):
    """
    This class launches the reports for the 4 metrics needed to
    calculate the global metrics, collects the results and
    writes them to storage.
    """

    show_in_ui = True

    def __init__(self,
                 cohort_id,
                 start_date,
                 end_date,
                 user_id=0):
        """
        Parameters:
            cohort_id       : ID of the cohort
            start_date      : Start date for the GlobalMetrics report
            end_date        : End date for the GlobalMetrics report
            user_id         : The user running this report
        """
        self.cohort_id = cohort_id
        self.start_date = start_date
        self.end_date = end_date
        self.user_id = user_id
        self.recurrent_parent_id = None
        self.persistent_id = None

    def run(self):
        """
        This initializes the cohort and any parameters not known at init time
        for this ReportNode, and initializes and calls it's super class' run method.

        Raises:
            KeyError if required parameters are missing
        """
        cohort_store_object = cohort_service.fetch_by_id(self.cohort_id)
        # First make sure this is a valid cohort
        if cohort_store_object is not None and cohort_store_object.validated:
            self.cohort = cohort_service.convert(cohort_store_object)
            validate_report = ValidateProgramMetricsReport(self.cohort,
                                                           db.get_session(),
                                                           user_id=self.user_id)
            self.cohort.size = validate_report.unique_users
            self.parameters = {
                'name': 'Program Global Metrics Report',
                'cohort': {
                    'id': self.cohort.id,
                    'name': self.cohort.name,
                    'size': self.cohort.size,
                },
                'user_id': self.user_id,
                'metric': {
                    'name': 'ProgramGlobalMetrics',
                    'end_date': self.end_date
                },
            }

            super(RunProgramMetricsReport, self).__init__(
                name=self.parameters['name'],
                user_id=self.user_id,
                parameters=self.parameters,
                public=False,
                recurrent=False,
                recurrent_parent_id=self.recurrent_parent_id,
                created=None,
                store=True,
                persistent_id=self.persistent_id,
            )
            
            if validate_report.valid():
                self.children = [self.get_active_editors_report(),
                                 self.get_new_editors_report(),
                                 self.get_pages_created_report(),
                                 self.get_pages_edited_report(),
                                 self.get_bytes_added_report()]
            else:
                self.children = [validate_report]
            return super(RunProgramMetricsReport, self).run()

        else:
            # This should never happen, unless it's a test where RunProgramMetricsReport
            # is being directly instantiated.
            task_logger.error("Cohort not validated")
            # Clean up cohort anyway
            cohort_service.delete_owner_cohort(None, self.cohort_id)
            raise Exception("Cohort not validated")

    def finish(self, aggregated_results):
        # Delete the cohort - we don't want to store these cohorts permanently
        cohort_service.delete_owner_cohort(None, self.cohort_id)
        if len(aggregated_results) > 1:
            # Get all the results into the desired shape and return them
            new_editors_count = aggregated_results[1][Aggregation.SUM]['newly_registered']

            # Existing editors can be calculated by subtracting the new editors count
            # from the size of the cohort, we calculate this here and add it to
            # the list of aggregated_results.
            existing_editors_count = self.cohort.size - new_editors_count
            aggregated_results.append({Aggregation.SUM:
                                       {'existing_editors': existing_editors_count}})

            # Manually rename absolute_sum to bytes_added - this looks silly, there
            # is probably a better way to do it
            bytes_added_count = aggregated_results[4][Aggregation.SUM]['absolute_sum']
            aggregated_results[4] = ({Aggregation.SUM:
                                      {'bytes_added': bytes_added_count}})

            # At this point aggregated_results is a list of dicts that looks like:
            # [{Aggregation.SUM: {'newly_registered':3}},
            #  {Aggregation.SUM: {'existing_editors':3}}]
            # We convert this into a single dict with key Sum,
            # and all the submetrics as values
            # Like: {Aggregation.SUM: {'newly_registered': 3, 'existing_editors': 3}}
            submetrics = [s[Aggregation.SUM] for s in aggregated_results]
            result = {}
            for s in submetrics:
                result.update(s)
            return self.report_result({Aggregation.SUM: result})
        else:
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

    def get_aggregate_by_user_report(self, parameters):
        metric_dict = parameters['metric']
        metric = metric_classes[metric_dict['name']](**metric_dict)
        return SumAggregateByUserReport(self.cohort,
                                        metric,
                                        parameters=parameters,
                                        user_id=self.user_id)

    def get_aggregate_report(self, parameters):
        metric_dict = parameters['metric']
        metric = metric_classes[metric_dict['name']](**metric_dict)
        return AggregateReport(metric,
                               self.cohort,
                               options=parameters['options'],
                               user_id=self.user_id)

    def get_active_editors_report(self):
        return self.get_aggregate_by_user_report({
            'name': 'Active Editors report',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
            },
            'metric': {
                'name': 'RollingActiveEditor',
                'end_date': self.start_date,
                'individualResults': True,
            },
        })

    def get_new_editors_report(self):
        return self.get_aggregate_by_user_report({
            'name': 'New Editors report',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
            },
            'metric': {
                'name': 'NewlyRegistered',
                'start_date': self.end_date - timedelta(weeks=2),
                'end_date': self.end_date,
                'individualResults': True,
            },
        })

    def get_pages_created_report(self):
        return self.get_aggregate_report({
            'name': 'Pages created report',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
            },
            'metric': {
                'name': 'PagesCreated',
                'namespaces': [0],
                'start_date': self.start_date,
                'end_date': self.end_date,
                'aggregateResults': True,
                'aggregateSum': True,
            },
            'options': {
                'aggregateResults': True,
                'aggregateSum': True,
            }
        })

    def get_pages_edited_report(self):
        return self.get_aggregate_by_user_report({
            'name': 'Pages Edited report',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
            },
            'metric': {
                'name': 'PagesEdited',
                'namespaces': [0],
                'start_date': self.start_date,
                'end_date': self.end_date,
                'aggregateResults': True,
                'aggregateSum': True,
            },
            'options': {
                'aggregateResults': True,
                'aggregateSum': True,
            }
        })

    def get_bytes_added_report(self):
        return self.get_aggregate_report({
            'name': 'Bytes Added report',
            'cohort': {
                'id': self.cohort.id,
                'name': self.cohort.name,
            },
            'metric': {
                'name': 'BytesAdded',
                'namespaces': [0],
                'start_date': self.start_date,
                'end_date': self.end_date,
                'aggregateResults': True,
                'aggregateSum': True,
                'absolute_sum': True,
                'negative_only_sum': False,
                'positive_only_sum': False,
                'net_sum': False,
            },
            'options': {
                'aggregateResults': True,
                'aggregateSum': True,
            }
        })
