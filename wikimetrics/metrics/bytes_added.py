from ..models import Revision, Page
from metric import Metric
from form_fields import BetterBooleanField, CommaSeparatedIntegerListField
from wtforms import DateField
from sqlalchemy import func, case
from sqlalchemy.sql.expression import label


__all__ = [
    'BytesAdded',
]


class BytesAdded(Metric):
    """
    This class implements bytes added logic.
    An instance of the class is callable and will compute four different aggregations of
    the bytes contributed or removed from a mediawiki instance:
        
        * net_sum: bytes added minus bytes removed
        * abs_sum: bytes added plus bytes removed
        * pos_sum: bytes added
        * neg_sum: bytes removed
    
    This sql query was used as a starting point for the sqlalchemy query:
    
     select sum(
                cast(r.rev_len as signed) - cast(coalesce(previous_r.rev_len, 0) as signed)
            ) as net_sum
            ,sum(
                abs(cast(r.rev_len as signed) - cast(coalesce(previous_r.rev_len, 0) as signed))
            ) as abs_sum
            ,sum(case
                when cast(r.rev_len as signed) - cast(coalesce(previous_r.rev_len, 0) as signed) > 0
                then cast(r.rev_len as signed) - cast(coalesce(previous_r.rev_len, 0) as signed)
                else 0
            end) as pos_sum
            ,sum(case
                when cast(r.rev_len as signed) - cast(coalesce(previous_r.rev_len, 0) as signed) < 0
                then abs(
                    cast(r.rev_len as signed) - cast(coalesce(previous_r.rev_len, 0) as signed)
                )
                else 0
            end) as neg_sum
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
    
    start_date      = DateField()
    end_date        = DateField()
    namespaces      = CommaSeparatedIntegerListField(default=[0], description='0, 2, 4, etc.')
    positive_total  = BetterBooleanField(default=True)
    negative_total  = BetterBooleanField(default=True)
    absolute_total  = BetterBooleanField(default=True)
    net_total       = BetterBooleanField(default=True)
    
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
        print bytes_added_by_user
        
        result_dict = {
            user_id: {
                'net_sum': net_sum,
                'absolute_sum': absolute_sum,
                'positive_only_sum': positive_only_sum,
                'negative_only_sum': negative_only_sum,
            }
            for user_id, net_sum, absolute_sum, positive_only_sum, negative_only_sum
            in bytes_added_by_user
        }
        return {user_id: result_dict.get(user_id, {
            'net_sum': None,
            'absolute_sum': None,
            'positive_only_sum': None,
            'negative_only_sum': None,
        }) for user_id in user_ids}
