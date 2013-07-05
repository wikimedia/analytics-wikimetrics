from metric import Metric
from flask.ext import wtf
from wtforms.compat import text_type

__all__ = [
    'BytesAdded',
]


def better_bool(value):
    if type(value) is bool:
        return value
    elif type(value) is list and len(value) > 0:
        value = value[0]
    else:
        return False
    
    return str(value).strip().lower() in ['yes', 'y', 'true']


class BetterBooleanField(wtf.BooleanField):
    
    def process_formdata(self, valuelist):
        # Checkboxes and submit buttons simply do not send a value when
        # unchecked/not pressed. So the actual value="" doesn't matter for
        # purpose of determining .data, only whether one exists or not.
        self.data = better_bool(valuelist)


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
    
    start_date      = wtf.DateField()
    end_date        = wtf.DateField()
    namespace       = wtf.IntegerField(default=0)
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
        return {user: None for user in user_ids}
