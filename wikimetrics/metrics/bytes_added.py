from datetime import date
from ..utils import thirty_days_ago
from ..models import Revision, Page
from metric import Metric
from form_fields import BetterBooleanField, CommaSeparatedIntegerListField
from wtforms.validators import Required
from wtforms import DateField
from sqlalchemy import func, case, between
from sqlalchemy.sql.expression import label


__all__ = [
    'BytesAdded',
]


class BytesAdded(Metric):
    """
    This class implements bytes added logic.
    An instance of the class is callable and will compute four different aggregations of
    the bytes contributed or removed from a mediawiki instance:
        
        * net_sum           : bytes added minus bytes removed
        * absolute_sum      : bytes added plus bytes removed
        * positive_only_sum : bytes added
        * negative_only_sum : bytes removed
    
    This sql query was used as a starting point for the sqlalchemy query:
    
     select sum(
                cast(r.rev_len as signed) - cast(coalesce(previous_r.rev_len, 0) as signed)
            ) as net_sum
            ,sum(
                abs(cast(r.rev_len as signed) - cast(coalesce(previous_r.rev_len, 0) as signed))
            ) as absolute_sum
            ,sum(case
                when cast(r.rev_len as signed) - cast(coalesce(previous_r.rev_len, 0) as signed) > 0
                then cast(r.rev_len as signed) - cast(coalesce(previous_r.rev_len, 0) as signed)
                else 0
            end) as positive_only_sum
            ,sum(case
                when cast(r.rev_len as signed) - cast(coalesce(previous_r.rev_len, 0) as signed) < 0
                then abs(
                    cast(r.rev_len as signed) - cast(coalesce(previous_r.rev_len, 0) as signed)
                )
                else 0
            end) as negative_only_sum
       from revision r
                inner join
            page p              on p.page_id = r.rev_page
                left join
            revision previous_r on previous_r.rev_id = r.rev_parent_id
      where p.page_namespace = [parametrized]
        and r.rev_timestamp between [start] and [end]
        and r.rev_user in ([parametrized])
    """
    show_in_ui  = True
    id          = 'bytes-added'
    label       = 'Bytes Added'
    description = 'Compute different aggregations of the bytes contributed or removed from a\
                   mediawiki project'
    
    start_date          = DateField(default=thirty_days_ago)
    end_date            = DateField(default=date.today)
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
        PreviousRevision = session.query(Revision).subquery()
        
        BC = session.query(
            Revision.rev_user,
            label('byte_change', Revision.rev_len - PreviousRevision.c.rev_len),
        )\
            .join(Page)\
            .outerjoin(PreviousRevision, Revision.rev_parent_id == PreviousRevision.c.rev_id)\
            .filter(Page.page_namespace.in_(self.namespaces.data))\
            .filter(Revision.rev_user.in_(user_ids))\
            .filter(between(Revision.rev_timestamp, self.start_date.data, self.end_date.data))\
            .subquery()
        
        bytes_added_by_user = session.query(
            BC.c.rev_user,
            func.sum(BC.c.byte_change).label('net_sum'),
            func.sum(func.abs(BC.c.byte_change)).label('absolute_sum'),
            func.sum(case(
                [(BC.c.byte_change > 0, BC.c.byte_change)], else_=0
            )).label('positive_only_sum'),
            func.sum(case(
                [(BC.c.byte_change < 0, BC.c.byte_change)], else_=0
            )).label('negative_only_sum'),
        )\
            .group_by(BC.c.rev_user)\
            .all()
        
        result_dict = {}
        for user_id, net, absolute, positive, negative in bytes_added_by_user:
            
            result_dict[user_id] = {}
            if self.net_sum.data:
                result_dict[user_id]['net_sum'] = net
            if self.absolute_sum.data:
                result_dict[user_id]['absolute_sum'] = absolute
            if self.positive_only_sum.data:
                result_dict[user_id]['positive_only_sum'] = positive
            if self.negative_only_sum.data:
                result_dict[user_id]['negative_only_sum'] = negative
        
        return {user_id: result_dict.get(user_id, {
            'net_sum': None,
            'absolute_sum': None,
            'positive_only_sum': None,
            'negative_only_sum': None,
        }) for user_id in user_ids}
