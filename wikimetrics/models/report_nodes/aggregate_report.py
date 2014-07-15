from math import sqrt
from decimal import Decimal
from collections import OrderedDict
from celery.utils.log import get_task_logger

from wikimetrics.utils import stringify, CENSORED, NO_RESULTS, r
from wikimetrics.enums import Aggregation
from report import ReportNode
from multi_project_metric_report import MultiProjectMetricReport


task_logger = get_task_logger(__name__)


class AggregateReport(ReportNode):
    """
    Represents the output-shaping node that looks at a
    single metric's results over a cohort and returns any combination of:
    
        * individual results
        * a sum of the individual results
        * an average over the individual results
        * the standard deviation over the individual results
    
    Whether or not to return these is controlled by parameters passed to the constructor.
    """
    
    show_in_ui = False
    
    def __init__(self, metric, cohort, options, *args, **kwargs):
        """
        Parameters:
            metric  : an instance of a Metric class
            cohort  : a logical cohort object
            options : a dictionary including the following booleans:
                individualResults
                aggregateResults
                aggregateSum
                aggregateAverage
                aggregateStandardDeviation
            args    : should include any parameters needed by ReportNode
            kwargs  : should include any parameters needed by ReportNode
        """
        super(AggregateReport, self).__init__(*args, **kwargs)
        
        self.individual = options.get('individualResults', False)
        self.aggregate = options.get('aggregateResults', True)
        self.aggregate_sum = options.get('aggregateSum', True)
        self.aggregate_average = options.get('aggregateAverage', False)
        self.aggregate_std_deviation = options.get('aggregateStandardDeviation', False)
        
        self.children = [MultiProjectMetricReport(cohort, metric, *args, **kwargs)]
    
    def finish(self, child_results):
        aggregated_results = dict()
        results_by_user = child_results[0]
        
        if self.aggregate:
            if self.aggregate_sum:
                aggregated_results[Aggregation.SUM] = self.calculate(
                    results_by_user,
                    Aggregation.SUM
                )
            if self.aggregate_average:
                aggregated_results[Aggregation.AVG] = self.calculate(
                    results_by_user,
                    Aggregation.AVG
                )
            if self.aggregate_std_deviation:
                if Aggregation.AVG not in aggregated_results:
                    average = self.calculate(results_by_user, Aggregation.AVG)
                else:
                    average = aggregated_results[Aggregation.AVG]
                aggregated_results[Aggregation.STD] = self.calculate(
                    results_by_user,
                    Aggregation.STD,
                    average=average
                )
        
        if self.individual:
            if NO_RESULTS in results_by_user:
                results_by_user = {}
            aggregated_results[Aggregation.IND] = results_by_user
        
        return aggregated_results
    
    def calculate(self, results_by_user, type_of_aggregate, average=None):
        # TODO: terrible redo this
        """
        Calculates one type of aggregate by just iterating over the individual results
        Takes into account that results and aggregates may be split up by timeseries
        Also makes sure to ignore censored records when appropriate
        
        Parameters
            list_of_results     : list of individual results
            type_of_aggregate   : can be SUM, AVG, STD
            average             : None by default but required when computing STD
        
        Returns
            The aggregate specified, computed at the timeseries level if applicable
        """
        aggregation = dict()
        helper = dict()
        for user_id in results_by_user.keys():
            for key in results_by_user[user_id]:
                # the CENSORED key indicates that this user has censored
                # results for this metric.  It is not aggregate-able
                if key == CENSORED:
                    continue
                
                value = results_by_user[user_id][key]
                value_is_not_censored = CENSORED not in results_by_user[user_id]\
                    or results_by_user[user_id][CENSORED] != 1
                
                # handle timeseries aggregation
                if isinstance(value, dict):
                    if key not in aggregation:
                        aggregation[key] = OrderedDict()
                        helper[key] = dict()
                    
                    for subkey in value:
                        if subkey not in aggregation[key]:
                            aggregation[key][subkey] = 0
                            helper[key][subkey] = dict()
                            helper[key][subkey]['sum'] = Decimal(0.0)
                            helper[key][subkey]['square_diffs'] = Decimal(0.0)
                            helper[key][subkey]['count'] = 0
                        
                        if value_is_not_censored and not value[subkey] is None:
                            helper[key][subkey]['sum'] += Decimal(value[subkey])
                            helper[key][subkey]['count'] += 1
                            if type_of_aggregate == Aggregation.STD:
                                diff = Decimal(value[subkey]) - average[key][subkey]
                                helper[key][subkey]['square_diffs'] += Decimal(
                                    pow(diff, 2)
                                )
                        
                        if type_of_aggregate == Aggregation.SUM:
                            aggregation[key][subkey] = r(helper[key][subkey]['sum'])
                        elif type_of_aggregate == Aggregation.AVG:
                            aggregation[key][subkey] = r(safe_average(
                                helper[key][subkey]['sum'],
                                helper[key][subkey]['count']
                            ))
                        elif type_of_aggregate == Aggregation.STD:
                            aggregation[key][subkey] = r(sqrt(safe_average(
                                helper[key][subkey]['square_diffs'],
                                helper[key][subkey]['count']
                            )))
                
                # handle normal aggregation
                else:
                    if key not in aggregation:
                        aggregation[key] = 0
                        helper[key] = dict()
                        helper[key]['sum'] = Decimal(0.0)
                        helper[key]['square_diffs'] = Decimal(0.0)
                        helper[key]['count'] = 0
                    
                    if value_is_not_censored and value is not None:
                        helper[key]['sum'] += Decimal(value)
                        helper[key]['count'] += 1
                        if type_of_aggregate == Aggregation.STD:
                            diff = Decimal(value) - average[key]
                            helper[key]['square_diffs'] += Decimal(pow(diff, 2))
                    
                    if type_of_aggregate == Aggregation.SUM:
                        aggregation[key] = r(helper[key]['sum'])
                    elif type_of_aggregate == Aggregation.AVG:
                        aggregation[key] = r(safe_average(
                            helper[key]['sum'],
                            helper[key]['count']
                        ))
                    elif type_of_aggregate == Aggregation.STD:
                        aggregation[key] = r(sqrt(safe_average(
                            helper[key]['square_diffs'],
                            helper[key]['count']
                        )))
        
        return aggregation
    
    def __repr__(self):
        return '<AggregateReport("{0}")>'.format(self.persistent_id)


def safe_average(cummulative_sum, count):
    if count != 0:
        return r(cummulative_sum / count)
    else:
        return 0
