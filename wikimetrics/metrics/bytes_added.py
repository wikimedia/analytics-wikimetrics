from ..utils import thirty_days_ago, today
from ..models import Revision, Page
from timeseries_metric import TimeseriesMetric
from form_fields import (
    BetterDateTimeField,
    BetterBooleanField,
    CommaSeparatedIntegerListField,
)
from wtforms.validators import Required
from sqlalchemy import func, case, cast, Integer
from sqlalchemy.sql.expression import label


__all__ = [
    'BytesAdded',
]


class BytesAdded(TimeseriesMetric):
    """
    This class implements bytes added logic.
    An instance of the class is callable and will compute four different aggregations of
    the bytes contributed or removed from a mediawiki instance:
        
        * net_sum           : bytes added minus bytes removed
        * absolute_sum      : bytes added plus bytes removed
        * positive_only_sum : bytes added
        * negative_only_sum : bytes removed
    
    This is the sql query that sqlalchemy generates from our Bytes Added logic
    
     SELECT anon_1.rev_user AS anon_1_rev_user,
            sum(anon_1.byte_change) AS net_sum,
            sum(abs(anon_1.byte_change)) AS absolute_sum,
            sum(CASE
                    WHEN (anon_1.byte_change > 0)
                    THEN anon_1.byte_change
                    ELSE 0 END
               ) AS positive_only_sum,
            sum(CASE
                    WHEN (anon_1.byte_change < 0)
                    THEN anon_1.byte_change
                    ELSE 0 END
               ) AS negative_only_sum
       FROM (SELECT revision.rev_user AS rev_user,
                    (   cast(revision.rev_len as signed)
                        - cast(coalesce(anon_2.rev_len, 0) as signed)
                    ) AS byte_change
               FROM revision
                        INNER JOIN
                    page        ON page.page_id = revision.rev_page
                        LEFT OUTER JOIN
                    (SELECT revision.rev_id AS rev_id,
                            revision.rev_len AS rev_len
                       FROM revision
                    ) AS anon_2 ON revision.rev_parent_id = anon_2.rev_id
              WHERE page.page_namespace IN ('0')
                AND revision.rev_user IN (3174352)
                AND revision.rev_timestamp BETWEEN '2013-06-18' AND '2013-07-18'
            ) AS anon_1
      GROUP BY anon_1.rev_user
    """
    show_in_ui  = True
    id          = 'bytes-added'
    label       = 'Bytes Added'
    description = 'Compute different aggregations of the bytes\
                   contributed or removed from a mediawiki project'
    
    namespaces          = CommaSeparatedIntegerListField(
        None,
        [Required()],
        default='0',
        description='0, 2, 4, etc.',
    )
    positive_only_sum   = BetterBooleanField(default=True)
    negative_only_sum   = BetterBooleanField(default=True)
    absolute_sum        = BetterBooleanField(default=True)
    net_sum             = BetterBooleanField(default=True)
    
    def __call__(self, user_ids, session):
        """
        Parameters:
            user_ids    : list of mediawiki user ids to find bytes added for
            session     : sqlalchemy session open on a mediawiki database
        
        Returns:
            dictionary from user ids to another dictionary with the following keys:
                * net_sum           : bytes added minus bytes removed
                * absolute_sum      : bytes added plus bytes removed
                * positive_only_sum : bytes added
                * negative_only_sum : bytes removed
        """
        start_date = self.start_date.data
        end_date = self.end_date.data
        
        PreviousRevision = session.query(Revision.rev_len, Revision.rev_id).subquery()
        BC = session.query(
            Revision.rev_user,
            Revision.rev_timestamp,
            label(
                'byte_change',
                cast(Revision.rev_len, Integer)
                -
                cast(func.coalesce(PreviousRevision.c.rev_len, 0), Integer)
            ),
        )\
            .join(Page)\
            .outerjoin(
                PreviousRevision,
                Revision.rev_parent_id == PreviousRevision.c.rev_id
            )\
            .filter(Page.page_namespace.in_(self.namespaces.data))\
            .filter(Revision.rev_user.in_(user_ids))\
            .filter(Revision.rev_timestamp > start_date)\
            .filter(Revision.rev_timestamp <= end_date)\
            .subquery()
        
        bytes_added_by_user = session.query(BC.c.rev_user).group_by(BC.c.rev_user)
        
        # add submetrics as columns to the output
        submetrics = []
        index = 1
        if self.net_sum.data:
            submetrics.append(('net_sum', index, 0))
            bytes_added_by_user = bytes_added_by_user.add_column(
                func.sum(BC.c.byte_change).label('net_sum')
            )
            index += 1
        
        if self.absolute_sum.data:
            submetrics.append(('absolute_sum', index, 0))
            bytes_added_by_user = bytes_added_by_user.add_column(
                func.sum(func.abs(BC.c.byte_change)).label('absolute_sum'),
            )
            index += 1
        
        if self.positive_only_sum.data:
            submetrics.append(('positive_only_sum', index, 0))
            bytes_added_by_user = bytes_added_by_user.add_column(
                func.sum(case(
                    [(BC.c.byte_change > 0, BC.c.byte_change)], else_=0
                )).label('positive_only_sum'),
            )
            index += 1
        
        if self.negative_only_sum.data:
            submetrics.append(('negative_only_sum', index, 0))
            bytes_added_by_user = bytes_added_by_user.add_column(
                func.sum(case(
                    [(BC.c.byte_change < 0, BC.c.byte_change)], else_=0
                )).label('negative_only_sum'),
            )
            index += 1
        
        query = self.apply_timeseries(bytes_added_by_user, rev=BC.c)
        return self.results_by_user(user_ids, query, submetrics, date_index=index)
