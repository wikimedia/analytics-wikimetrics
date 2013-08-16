from wikimetrics.configurables import db
from wikimetrics.models.cohort_user import CohortUserRole
from wikimetrics.models.cohort import Cohort
from wikimetrics.models.user import User
from wikimetrics.models.cohort_user import CohortUser
from wikimetrics.metrics import metric_classes
from wikimetrics.utils import deduplicate
from report import ReportNode
from aggregate_report import AggregateReport


__all__ = ['RunReport']


class RunReport(ReportNode):
    """
    Represents a batch of cohort-metric reports created by the
    user during a single reports/create/ workflow.  This is also
    intended to be the unit of work which could be easily re-run.
    """
    
    show_in_ui = False
    
    def __init__(self, desired_responses, user_id=0, *args, **kwargs):
        """
        Parameters:
            desired_responses : list of dictionaries of the form:
                cohort: the cohort to run a metric on
                metric: the metric to run
                aggregation: the aggregation options to use
        """
        super(RunReport, self).__init__(user_id=user_id, *args, **kwargs)
        self.parse_request(desired_responses)
    
    def parse_request(self, desired_responses):
        children = []
        metric_names = []
        cohort_names = []
        allowed_roles = [CohortUserRole.OWNER, CohortUserRole.VIEWER]
        for cohort_metric_dict in desired_responses:
            
            # get cohort
            cohort_dict = cohort_metric_dict['cohort']
            db_session = db.get_session()
            cohort = db_session.query(Cohort)\
                .join(CohortUser)\
                .join(User)\
                .filter(User.id == self.user_id)\
                .filter(Cohort.id == cohort_dict['id'])\
                .filter(Cohort.enabled)\
                .filter(CohortUser.role.in_(allowed_roles))\
                .one()
            db_session.close()
            
            # construct metric
            metric_dict = cohort_metric_dict['metric']
            class_name = metric_dict['name']
            metric_class = metric_classes[class_name]
            metric = metric_class(**metric_dict)
            # TODO: don't think csrf can work here, but see if there's another way
            metric.fake_csrf()
            if metric.validate():
                # construct and start RunReport
                output_child = AggregateReport(
                    cohort,
                    metric,
                    individual=metric_dict['individualResults'],
                    aggregate=metric_dict['aggregateResults'],
                    aggregate_sum=metric_dict['aggregateSum'],
                    aggregate_average=metric_dict['aggregateAverage'],
                    aggregate_std_deviation=metric_dict['aggregateStandardDeviation'],
                    name=cohort_metric_dict['name'],
                    user_id=self.user_id,
                )
                children.append(output_child)
                metric_names.append(metric.label)
                cohort_names.append(cohort.name)
            else:
                raise Exception('{0} was incorrectly configured'.format(metric.label))
        
        metric_names = deduplicate(metric_names)
        cohort_names = deduplicate(cohort_names)
        
        self.name = ', '.join(metric_names) + ' for ' + ', '.join(cohort_names)
        self.children = children
    
    def finish(self, aggregated_results):
        result = self.report_result('Finished', child_results=aggregated_results)
        return result
    
    def __repr__(self):
        return '<RunReport("{0}")>'.format(self.persistent_id)
