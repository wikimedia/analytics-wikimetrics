from sqlalchemy import func
from sqlalchemy.sql.expression import label
from wtforms.validators import Required

from wikimetrics.utils import thirty_days_ago, today
from wikimetrics.forms.fields import CommaSeparatedIntegerListField, BetterBooleanField
from wikimetrics.models import Page, Revision, Archive
from timeseries_metric import TimeseriesMetric


class PagesCreated(TimeseriesMetric):
    """
    This class counts the pages created by editors over a period of time.

    This sql query was used as a starting point for the sqlalchemy query:

    SELECT count(*)
    FROM <database>.revision
    JOIN <database>.page
        ON rev_page = page_id
    WHERE rev_parent_id = 0
        AND <where>
        AND rev_user = %(user)s
        AND rev_timestamp > %(start)s
        AND rev_timestamp <= %(end)s
    """
    
    show_in_ui  = True
    id          = 'pages_created'
    label       = 'Pages Created'
    category    = 'Content'
    description = (
        'Compute the number of pages created by each \
         editor in a time interval'
    )
    default_result  = {
        'pages_created': 0,
    }

    include_deleted = BetterBooleanField(
        default=True,
        description='Count pages that have been deleted',
    )
    namespaces = CommaSeparatedIntegerListField(
        None,
        default='0',
        description='0, 2, 4, etc. (leave blank for *all*)',
    )
    
    def __call__(self, user_ids, session):
        """
        Parameters:
            user_ids    : list of mediawiki user ids to find edit for
            session     : sqlalchemy session open on a mediawiki database
        
        Returns:
            dictionary from user ids to the number of edit found.
        """
        # TODO: (low-priority) take into account cases where rev_deleted = 1
        start_date = self.start_date.data
        end_date = self.end_date.data
        
        revisions = session\
            .query(
                label('user_id', Revision.rev_user),
                label('timestamp', Revision.rev_timestamp)
            )\
            .filter(Revision.rev_parent_id == 0)\
            .filter(Revision.rev_timestamp > start_date)\
            .filter(Revision.rev_timestamp <= end_date)

        archives = session\
            .query(
                label('user_id', Archive.ar_user),
                label('timestamp', Archive.ar_timestamp)
            )\
            .filter(Archive.ar_parent_id == 0)\
            .filter(Archive.ar_timestamp > start_date)\
            .filter(Archive.ar_timestamp <= end_date)

        if self.namespaces.data and len(self.namespaces.data) > 0:
            revisions = revisions.join(Page)\
                .filter(Page.page_namespace.in_(self.namespaces.data))
            archives = archives\
                .filter(Archive.ar_namespace.in_(self.namespaces.data))

        revisions = self.filter(revisions, user_ids, column=Revision.rev_user)
        archives = self.filter(archives, user_ids, column=Archive.ar_user)

        both = revisions
        if self.include_deleted.data:
            both = both.union_all(archives)
        both = both.subquery()

        query = session.query(both.c.user_id, func.count())\
            .group_by(both.c.user_id)

        query = self.apply_timeseries(query, column=both.c.timestamp)

        return self.results_by_user(
            user_ids,
            query,
            [(self.id, 1, 0)],
            date_index=2,
        )
