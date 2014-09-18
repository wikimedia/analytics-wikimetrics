from sqlalchemy import func
from sqlalchemy.sql.expression import label
from wtforms.validators import Required

from wikimetrics.utils import thirty_days_ago, today
from wikimetrics.models import Page, Revision, Archive
from wikimetrics.forms.fields import CommaSeparatedIntegerListField
from timeseries_metric import TimeseriesMetric


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
    category    = 'Content'
    description = (
        'Compute the number of edits in a specific'
        'namespace of a mediawiki project'
    )
    default_result  = {
        'edits': 0,
    }

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

        revisions = session\
            .query(
                label('user_id', Revision.rev_user),
                label('timestamp', Revision.rev_timestamp)
            )\
            .join(Page)\
            .filter(Page.page_namespace.in_(self.namespaces.data))\
            .filter(Revision.rev_timestamp > start_date)\
            .filter(Revision.rev_timestamp <= end_date)

        archives = session\
            .query(
                label('user_id', Archive.ar_user),
                label('timestamp', Archive.ar_timestamp)
            )\
            .filter(Archive.ar_namespace.in_(self.namespaces.data))\
            .filter(Archive.ar_timestamp > start_date)\
            .filter(Archive.ar_timestamp <= end_date)

        revisions = self.filter(revisions, user_ids, column=Revision.rev_user)
        archives = self.filter(archives, user_ids, column=Archive.ar_user)

        both = revisions.union_all(archives).subquery()

        query = session.query(both.c.user_id, func.count())\
            .group_by(both.c.user_id)

        query = self.apply_timeseries(query, column=both.c.timestamp)

        return self.results_by_user(
            user_ids,
            query,
            [(self.id, 1, 0)],
            date_index=2,
        )
