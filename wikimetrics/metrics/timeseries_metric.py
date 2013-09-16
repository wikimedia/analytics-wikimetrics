from sqlalchemy import func
from datetime import datetime
from wtforms import SelectField
from metric import Metric
from wikimetrics.models import Revision


__all__ = ['TimeseriesChoices', 'TimeseriesMetric']


class TimeseriesChoices(object):
    NONE = 'none'
    HOUR = 'hour'
    DAY = 'day'
    MONTH = 'month'
    YEAR = 'year'


class TimeseriesMetric(Metric):
    """
    This class is the parent of Metric implementations which can return timeseries
    results.  It provides a single WTForm field to allow configuration of timeseries
    output.
    """
    
    timeseries = SelectField(
        'Time Series by',
        default=TimeseriesChoices.NONE,
        choices=[
            (TimeseriesChoices.NONE, TimeseriesChoices.NONE),
            (TimeseriesChoices.HOUR, TimeseriesChoices.HOUR),
            (TimeseriesChoices.DAY, TimeseriesChoices.DAY),
            (TimeseriesChoices.MONTH, TimeseriesChoices.MONTH),
            (TimeseriesChoices.YEAR, TimeseriesChoices.YEAR),
        ],
    )
    
    def apply_timeseries(self, query):
        """
        Take a query and slice it up into equal time intervals
        
        Parameters
            query               : a sql alchemy query
        
        Returns
            The query parameter passed in, with a grouping by the desired time slice
        """
        choice = self.timeseries.data
        
        if choice == TimeseriesChoices.NONE:
            return query
        
        query = query.add_column(func.year(Revision.rev_timestamp))
        query = query.group_by(func.year(Revision.rev_timestamp))
        
        if choice == TimeseriesChoices.YEAR:
            return query
        
        query = query.add_column(func.month(Revision.rev_timestamp))
        query = query.group_by(func.month(Revision.rev_timestamp))
        
        if choice == TimeseriesChoices.MONTH:
            return query
        
        query = query.add_column(func.day(Revision.rev_timestamp))
        query = query.group_by(func.day(Revision.rev_timestamp))
        
        if choice == TimeseriesChoices.DAY:
            return query
        
        query = query.add_column(func.hour(Revision.rev_timestamp))
        query = query.group_by(func.hour(Revision.rev_timestamp))
        
        if choice == TimeseriesChoices.HOUR:
            return query
    
    def get_date_from_tuple(self, row_tuple, start_index, stop_index):
        date_pieces = row_tuple[start_index:stop_index]
        date_string = ''
        if len(date_pieces) > 0:
            date_string += str(date_pieces[0])
        if len(date_pieces) > 1:
            date_string += '-'
            date_string += str(date_pieces[1]).rjust(2, '0')
        if len(date_pieces) > 2:
            date_string += '-'
            date_string += str(date_pieces[2]).rjust(2, '0')
        if len(date_pieces) > 3:
            date_string += ' '
            date_string += str(date_pieces[3]).rjust(2, '0')
            date_string += ':00:00'
        
        return date_string
