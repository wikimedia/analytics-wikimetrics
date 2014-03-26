from math import sqrt
from decimal import Decimal
from collections import OrderedDict
from celery.utils.log import get_task_logger

from wikimetrics.utils import stringify, CENSORED, r
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
        result_values = [res.values() for res in result_dicts]
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
                if Aggregation.AVG not in aggregated_results:
                    average = self.calculate(child_results, Aggregation.AVG)
                else:
                    average = aggregated_results[Aggregation.AVG]
                aggregated_results[Aggregation.STD] = self.calculate(
                    child_results,
                    Aggregation.STD,
                    average=average
                )
        
        if self.individual:
            aggregated_results[Aggregation.IND] = child_results
        
        result = self.report_result(aggregated_results, child_results=result_dicts)
        return result
    
    def calculate(self, list_of_results, type_of_aggregate, average=None):
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
        for results_by_user in list_of_results:
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
