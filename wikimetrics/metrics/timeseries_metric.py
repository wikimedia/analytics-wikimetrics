from collections import OrderedDict
from sqlalchemy import func
from datetime import datetime
from dateutil.relativedelta import relativedelta
from wtforms import SelectField

from wikimetrics.models import Revision
from wikimetrics.utils import thirty_days_ago, today, format_pretty_date
from wikimetrics.enums import TimeseriesChoices
from wikimetrics.forms.fields import CommaSeparatedIntegerListField, BetterDateTimeField
from wikimetrics.forms.validators import NotGreater
from metric import Metric


class TimeseriesMetric(Metric):
    """
    This class is the parent of Metric implementations which can return timeseries
    results.  It provides a single WTForm field to allow configuration of timeseries
    output.
    """
    
    start_date  = BetterDateTimeField(
        default=thirty_days_ago, validators=[NotGreater('end_date')])
    end_date    = BetterDateTimeField(default=today)
    timeseries  = SelectField(
        'Time Series by',
        default=TimeseriesChoices.NONE,
        choices=[
            (TimeseriesChoices.NONE, TimeseriesChoices.NONE),
            (TimeseriesChoices.HOUR, TimeseriesChoices.HOUR),
            (TimeseriesChoices.DAY, TimeseriesChoices.DAY),
            (TimeseriesChoices.MONTH, TimeseriesChoices.MONTH),
            (TimeseriesChoices.YEAR, TimeseriesChoices.YEAR),
        ],
        description='Report results by year, month, day, or hour',
    )
    
    def apply_timeseries(self, query, column=Revision.rev_timestamp):
        """
        Take a query and slice it up into equal time intervals
        
        Parameters
            query   : a sql alchemy query
            column  : defaults to Revision.rev_timestamp, specifies the timestamp
                      column to use for the timeseries
        
        Returns
            The query parameter passed in, with a grouping by the desired time slice
        """
        choice = self.timeseries.data
        
        if choice == TimeseriesChoices.NONE:
            return query
        
        query = query.add_column(func.year(column))
        query = query.group_by(func.year(column))
        
        if choice == TimeseriesChoices.YEAR:
            return query
        
        query = query.add_column(func.month(column))
        query = query.group_by(func.month(column))
        
        if choice == TimeseriesChoices.MONTH:
            return query
        
        query = query.add_column(func.day(column))
        query = query.group_by(func.day(column))
        
        if choice == TimeseriesChoices.DAY:
            return query
        
        query = query.add_column(func.hour(column))
        query = query.group_by(func.hour(column))
        
        if choice == TimeseriesChoices.HOUR:
            return query
    
    def results_by_user(self, user_ids, query, submetrics, date_index=None):
        """
        Get results by user for a timeseries-enabled metric
        
        Parameters
            user_ids            : list of integer ids to return results for
            query               : sqlalchemy query to fetch results
            submetrics          : list of tuples of the form (label, index, default)
            date_index          : index of the year date part in the result row,
                                  in case this is a timeseries query
        
        Returns
            A dictionary of user_ids to results, shaped depending on timeseries:
            user_id: {
                'submetric 1': {
                    'date slice 1': submetric_1_value,
                    'date slice 2': submetric_1_value,
                    ...
                },
                'submetric 2': ...
                
                OR
                
                'submetric 1': submetric_1_value,
                'submetric 2': submetric_2_value,
                ...
            }
        """
        # get a dictionary of user_ids to their metric results
        results = self.submetrics_by_user(query, submetrics, date_index)
        
        # default user_ids to all the user ids in the results, if not present
        if user_ids and len(user_ids):
            if len(results.keys()) > len(user_ids):
                raise Exception('Filtering did not work properly')
        else:
            user_ids = results.keys()

        # make a default return dictionary for users not found by the query
        submetric_defaults = dict()
        for label, index, default in submetrics:
            if self.timeseries.data == TimeseriesChoices.NONE:
                submetric_defaults[label] = default
            else:
                submetric_defaults[label] = dict()
        
        # populate users not found by the query with the default created above
        results = {
            user_id: results.get(user_id, submetric_defaults)
            for user_id in user_ids
        }
        
        # in timeseries results, fill in missing date-times
        results = self.normalize_datetime_slices(results, submetrics)
        return results
    
    def submetrics_by_user(self, query, submetrics, date_index=None):
        """
        Same as results_by_user, except doesn't return results for users not found in
        the query_results list.
        """
        query_results = query.all()
        results = OrderedDict()
        
        # handle simple cases (no results or no timeseries)
        if not query_results:
            return results
        
        # get results by user and by date
        for row in query_results:
            user_id = row[0]
            if user_id not in results:
                results[user_id] = OrderedDict()
            
            date_slice = None
            if self.timeseries.data != TimeseriesChoices.NONE:
                date_slice = self.get_date_from_tuple(row, date_index, len(row))
            
            for label, index, default in submetrics:
                if date_slice:
                    if label not in results[user_id]:
                        results[user_id][label] = dict()
                    results[user_id][label][date_slice] = row[index]
                else:
                    results[user_id][label] = row[index]
        
        return results
    
    def normalize_datetime_slices(self, results_by_user, submetrics):
        """
        Starting from a sparse set of timeseries results, fill in default values
        for the specified list of sub-metrics.  Also make sure the chronological
        first timeseries slice is >= self.start_date.
        If self.timeseries is NONE, this is a simple identity function.
        
        Parameters
            results_by_user : dictionary of submetrics dictionaries by user
            submetrics      : list of tuples of the form (label, index, default)
        
        Returns
            the results, filled in with default values
        """
        if self.timeseries.data == TimeseriesChoices.NONE:
            return results_by_user
        
        slice_delta = self.get_delta_from_choice()
        timeseries_slices = OrderedDict()
        start_slice_key = format_pretty_date(self.start_date.data)
        timeseries_slices[start_slice_key] = None
        
        first_slice = self.get_first_slice()
        first_slice_key = format_pretty_date(first_slice)
        slice_to_default = first_slice
        while slice_to_default < self.end_date.data:
            date_key = format_pretty_date(slice_to_default)
            timeseries_slices[date_key] = None
            slice_to_default += slice_delta
        
        for user_id, user_submetrics in results_by_user.iteritems():
            for label, i, default in submetrics:
                if not label or not user_submetrics or label not in user_submetrics:
                    continue
                defaults = timeseries_slices.copy()
                defaults.update(user_submetrics[label])
                for k, v in defaults.iteritems():
                    if not v:
                        defaults[k] = default
                
                if start_slice_key != first_slice_key:
                    # coerce the first datetime slice to be self.start_date
                    defaults[start_slice_key] = defaults.pop(first_slice_key)
                
                user_submetrics[label] = defaults
        
        return results_by_user
    
    def get_first_slice(self):
        """
        Given a user's choice of timeseries grouping, and the value of the start_date,
        return the first interval in the timeseries
        """
        if self.timeseries.data == TimeseriesChoices.NONE:
            return None
        
        d = self.start_date.data
        if self.timeseries.data == TimeseriesChoices.HOUR:
            return datetime(d.year, d.month, d.day, d.hour)
        if self.timeseries.data == TimeseriesChoices.DAY:
            return datetime(d.year, d.month, d.day, 0)
        if self.timeseries.data == TimeseriesChoices.MONTH:
            return datetime(d.year, d.month, 1, 0)
        if self.timeseries.data == TimeseriesChoices.YEAR:
            return datetime(d.year, 1, 1, 0)
    
    def get_delta_from_choice(self):
        """
        Given a user's choice of timeseries grouping,
        return a delta that would be one "slice" wide
        """
        if self.timeseries.data == TimeseriesChoices.NONE:
            return relativedelta(hours=0)
        if self.timeseries.data == TimeseriesChoices.HOUR:
            return relativedelta(hours=1)
        if self.timeseries.data == TimeseriesChoices.DAY:
            return relativedelta(days=1)
        if self.timeseries.data == TimeseriesChoices.MONTH:
            return relativedelta(months=1)
        if self.timeseries.data == TimeseriesChoices.YEAR:
            return relativedelta(years=1)
    
    def get_date_from_tuple(self, row_tuple, start_index, stop_index):
        """
        Suppose you have a tuple like this:
        ([data], [data], ... , year, month, day, [data], [data])
        Then this function will parse out the year, month, day, and hour
        into a date string.  Anything beyond year, month, day is optional.
        """
        date_pieces = row_tuple[start_index:stop_index]
        year, month, day, hour = 1970, 1, 1, 0
        
        if len(date_pieces) > 0:
            year = date_pieces[0]
        if len(date_pieces) > 1:
            month = date_pieces[1]
        if len(date_pieces) > 2:
            day = date_pieces[2]
        if len(date_pieces) > 3:
            hour = date_pieces[3]
        
        return format_pretty_date(datetime(year, month, day, hour))
