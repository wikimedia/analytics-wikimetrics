from wtforms import SelectField
from metric import Metric


__all__ = ['TimeseriesChoices', 'TimeseriesMetric']


class TimeseriesChoices(object):
    NONE =  'none'
    HOUR =  'hour'
    DAY =   'day'
    WEEK =  'week'
    MONTH = 'month'
    YEAR =  'year'


class TimeseriesMetric(Metric):
    """
    This class is the parent of Metric implementations which can return timeseries
    results.  It provides a single WTForm field to allow configuration of timeseries
    output.
    """
    
    timeseries = SelectField('Time Series by', choices=[
        TimeseriesChoices.NONE,
        TimeseriesChoices.HOUR,
        TimeseriesChoices.DAY,
        TimeseriesChoices.WEEK,
        TimeseriesChoices.MONTH,
        TimeseriesChoices.YEAR,
    ])
    
    @staticmethod
    def apply_timeseries(query, timeseries_choice):
        """
        Take a query and slice it up into equal time intervals
        
        Parameters
            query               : a sql alchemy query
            timeseries_choice   : a TimeseriesChoices value
        
        Returns
            The query parameter passed in, with a grouping by the desired time slice
        """
        pass
