from metric import Metric
from datetime import date
from ..utils import thirty_days_ago
from form_fields import CommaSeparatedIntegerListField
from wtforms import DateField
from wtforms.validators import Required

__all__ = [
    'RevertRate',
]


class RevertRate(Metric):
    """
    This class implements revert rate logic.
    An instance of the class is callable and will compute the number of reverted
    edits for each user in a passed-in list.
    
    This sql query was used as a starting point for the sqlalchemy query:
    
     select r.rev_user, r.count(*)
       from revision r
      where r.rev_timestamp between [start] and [end]
        and r.rev_user in ([cohort's user list or maybe a join to a temp])
        and exists (
             select *
               from revision r1
                        inner join
                    revision r2     on r2.rev_sha1 = r1.rev_sha1
              where r1.rev_page = r.rev_page
                and r2.rev_page = r.rev_page
                and r1.rev_timestamp between [start] and r.rev_timestamp
                and r2.rev_timestamp between r.rev_timestamp and [end]
            )
      group by rev_user
    """
    
    show_in_ui  = True
    id          = 'revert-rate'
    label       = 'Revert Rate'
    description = 'Compute the number of reverted edits in a mediawiki project'
    
    start_date  = DateField(default=thirty_days_ago)
    end_date    = DateField(default=date.today)
    namespaces  = CommaSeparatedIntegerListField(
        None,
        [Required()],
        default='0',
        description='0, 2, 4, etc.',
    )
    
    def __call__(self, user_ids, session):
        """
        Parameters:
            user_ids    : list of mediawiki user ids to find edit reverts for
            session     : sqlalchemy session open on a mediawiki database
        
        Returns:
            dictionary from user ids to the number of edit reverts found.
        """
        return {user: None for user in user_ids}
