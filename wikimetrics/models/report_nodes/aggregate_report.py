from collections import OrderedDict
from decimal import Decimal
from celery.utils.log import get_task_logger

from wikimetrics.utils import stringify, CENSORED
from report import ReportNode
from multi_project_metric_report import MultiProjectMetricReport


__all__ = ['AggregateReport', 'Aggregation']

task_logger = get_task_logger(__name__)


class Aggregation(object):
    IND = 'Individual Results'
    SUM = 'Sum'
    AVG = 'Average'
    STD = 'Standard Deviation'


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
    
    show_in_ui = True
    
    def __init__(
        self,
        cohort,
        metric,
        individual=False,
        aggregate=True,
        aggregate_sum=True,
        aggregate_average=False,
        aggregate_std_deviation=False,
        *args,
        **kwargs
    ):
        super(AggregateReport, self).__init__(
            parameters=stringify(metric.data),
            *args,
            **kwargs
        )
        
        self.individual = individual
        self.aggregate = aggregate
        self.aggregate_sum = aggregate_sum
        self.aggregate_average = aggregate_average
        self.aggregate_std_deviation = aggregate_std_deviation
        
        self.children = [MultiProjectMetricReport(
            cohort,
            metric,
            name=self.name,
        )]
    
    def finish(self, result_dicts):
        aggregated_results = dict()
        task_logger.info(str(result_dicts))
        result_values = [r.values() for r in result_dicts]
        child_results = [result for sublist in result_values for result in sublist]
        
        if self.aggregate:
            if self.aggregate_sum:
                aggregated_results[Aggregation.SUM] = self.calculate(
                    child_results,
                    Aggregation.SUM
                )
            if self.aggregate_average:
                aggregated_results[Aggregation.AVG] = self.calculate(
                    child_results,
                    Aggregation.AVG
                )
            if self.aggregate_std_deviation:
                aggregated_results[Aggregation.STD] = self.calculate(
                    child_results,
                    Aggregation.STD
                )
        
        if self.individual:
            aggregated_results[Aggregation.IND] = child_results
        
        result = self.report_result(aggregated_results, child_results=result_dicts)
        return result
    
    def calculate(self, list_of_results, type_of_aggregate):
        # TODO: terrible redo this
        aggregation = dict()
        helper = dict()
        for results_by_user in list_of_results:
            for user_id in results_by_user.keys():
                for key in results_by_user[user_id]:
                    # the CENSORED key indicates that this user has censored
                    # results for this metric.  It is not aggregate-able
                    if key == CENSORED:
                        continue
                    
                    value = results_by_user[user_id][key]
                    value_is_not_censored = not CENSORED in results_by_user[user_id]\
                        or results_by_user[user_id][CENSORED] != 1
                    
                    if not value:
                        # NOTE: value should never be None in a timeseries result
                        value = Decimal(0)
                    
                    # handle timeseries aggregation
                    if isinstance(value, dict):
                        if not key in aggregation:
                            aggregation[key] = OrderedDict()
                            helper[key] = dict()
                        
                        for subkey in value:
                            if not subkey in aggregation[key]:
                                aggregation[key][subkey] = 0
                                helper[key][subkey] = dict()
                                helper[key][subkey]['sum'] = Decimal(0.0)
                                helper[key][subkey]['count'] = 0
                            
                            if value_is_not_censored:
                                value_subkey = value[subkey] or Decimal(0)
                                helper[key][subkey]['sum'] += Decimal(value_subkey)
                                helper[key][subkey]['count'] += 1
                            
                            if type_of_aggregate == Aggregation.SUM:
                                aggregation[key][subkey] = round(
                                    helper[key][subkey]['sum'],
                                    4
                                )
                            elif type_of_aggregate == Aggregation.AVG:
                                cummulative_sum = helper[key][subkey]['sum']
                                count = helper[key][subkey]['count']
                                if count != 0:
                                    aggregation[key][subkey] = round(
                                        cummulative_sum / count,
                                        4
                                    )
                                else:
                                    aggregation[key][subkey] = None
                            elif type_of_aggregate == Aggregation.STD:
                                aggregation[key][subkey] = 'Not Implemented'
                                pass
                    
                    # handle normal aggregation
                    else:
                        if not key in aggregation:
                            aggregation[key] = 0
                            helper[key] = dict()
                            helper[key]['sum'] = Decimal(0.0)
                            helper[key]['count'] = 0
                        
                        if value_is_not_censored:
                            helper[key]['sum'] += Decimal(value)
                            helper[key]['count'] += 1
                        
                        if type_of_aggregate == Aggregation.SUM:
                            aggregation[key] = round(
                                helper[key]['sum'],
                                4
                            )
                        elif type_of_aggregate == Aggregation.AVG:
                            count = helper[key]['count']
                            if count != 0:
                                aggregation[key] = round(
                                    helper[key]['sum'] / count,
                                    4
                                )
                            else:
                                aggregation[key] = None
                        elif type_of_aggregate == Aggregation.STD:
                            aggregation[key] = 'Not Implemented'
                            pass
        
        return aggregation
    
    def __repr__(self):
        return '<AggregateReport("{0}")>'.format(self.persistent_id)
