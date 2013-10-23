from sqlalchemy import func
from timeseries_metric import TimeseriesMetric, TimeseriesChoices
from form_fields import CommaSeparatedIntegerListField
from wtforms.validators import Required
from wikimetrics.utils import thirty_days_ago, today
from wikimetrics.models import Page, Revision


__all__ = [
    'NamespaceEdits',
]


class NamespaceEdits(TimeseriesMetric):
    """
    This class implements namespace edits logic.
    An instance of the class is callable and will compute the number of edits
    for each user in a passed-in list.
    
    This sql query was used as a starting point for the sqlalchemy query:
    
     select r.rev_user, r.count(*)
       from revision r
                inner join
            page p      on p.page_id = r.rev_page
      where r.rev_timestamp between [start] and [end]
        and r.rev_user in ([parameterized])
        and p.page_namespace in ([parameterized])
      group by rev_user
    """
    
    show_in_ui  = True
    id          = 'edits'
    label       = 'Edits'
    description = (
        'Compute the number of edits in a specific'
        'namespace of a mediawiki project'
    )
    
    namespaces = CommaSeparatedIntegerListField(
        None,
        [Required()],
        default='0',
        description='0, 2, 4, etc.',
    )
    
    def __call__(self, user_ids, session):
        """
        Parameters:
            user_ids    : list of mediawiki user ids to find edit for
            session     : sqlalchemy session open on a mediawiki database
        
        Returns:
            dictionary from user ids to the number of edit found.
        """
        start_date = self.start_date.data
        end_date = self.end_date.data
        
        query = session\
            .query(Revision.rev_user, func.count(Revision.rev_id))\
            .join(Page)\
            .filter(Page.page_namespace.in_(self.namespaces.data))\
            .filter(Revision.rev_user.in_(user_ids))\
            .filter(Revision.rev_timestamp > start_date)\
            .filter(Revision.rev_timestamp <= end_date)\
            .group_by(Revision.rev_user)
        
        query = self.apply_timeseries(query)
        return self.results_by_user(
            user_ids,
            query,
            [('edits', 1, 0)],
            date_index=2,
        )
