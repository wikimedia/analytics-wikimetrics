from sqlalchemy import func
from sqlalchemy.sql.expression import label, literal_column

from wikimetrics.utils import thirty_days_ago, today
from wikimetrics.models import Page, Revision, Archive
from wikimetrics.forms.fields import (
    CommaSeparatedIntegerListField,
    BetterBooleanField, BetterDateTimeField
)
from metric import Metric

ROLLUP_USER_ID = -1


class PagesEdited(Metric):
    """
    This class counts the pages edited by editors over a period of time.
    This sql query was used as a starting point for the sqlalchemy query:

    SELECT user_id, COUNT(*)
    FROM (
        SELECT DISTINCT user_id, page_id
        FROM (
            SELECT r.rev_user AS user_id, r.rev_page AS page_id
            FROM revision r
                INNER JOIN page p ON p.page_id = r.rev_page
            WHERE r.rev_timestamp BETWEEN [start] AND [end]
            AND r.rev_user in ([parameterized])
            AND p.page_namespace in ([parameterized])

            UNION ALL

            SELECT a.ar_user AS user_id, a.ar_page_id AS page_id
            FROM archive a
            WHERE a.ar_timestamp BETWEEN [start] AND [end]
            AND a.ar_user in ([parameterized])
            AND a.ar_namespace in ([parameterized])
        ) AS subq1
    ) AS subq2 GROUP BY user_id;
    """

    # NOTE: this is not enabled in the UI yet, but could be easily
    # The deduplicate parameter's a bit confusing, maybe consider
    # re-wording that when making this metric available
    show_in_ui  = False
    id          = 'pages_edited'
    label       = 'Pages Edited'
    category    = 'Content'
    description = (
        'Compute the number of unique pages edited by the'
        'cohort\'s users within a time interval'
    )
    default_result = {'pages_edited': 0}

    start_date  = BetterDateTimeField(default=thirty_days_ago)
    end_date    = BetterDateTimeField(default=today)

    include_deleted = BetterBooleanField(
        default=True,
        description='Count pages that have been deleted',
    )
    namespaces = CommaSeparatedIntegerListField(
        None,
        description='0, 2, 4, etc. (leave blank for *all*)',
    )
    deduplicate_across_users = BetterBooleanField(
        default=False,
        description='Count unique pages edited by the entire cohort,'
                    ' rolled up to one number.',
    )

    def __call__(self, user_ids, session):
        """
        Parameters:
            user_ids    : list of mediawiki user ids to find pages for
            session     : sqlalchemy session open on a mediawiki database

        Returns:
            dictionary from user ids to the number of pages edited found
        """
        start_date = self.start_date.data
        end_date = self.end_date.data
        deduplicate = self.deduplicate_across_users.data

        revisions = (
            session.query(
                label('user_id', Revision.rev_user),
                label('page_id', Revision.rev_page),
                label('timestamp', Revision.rev_timestamp)
            )
            .filter(Revision.rev_timestamp > start_date)
            .filter(Revision.rev_timestamp <= end_date))

        archives = (
            session.query(
                label('user_id', Archive.ar_user),
                label('page_id', Archive.ar_page_id),
                label('timestamp', Archive.ar_timestamp)
            )
            .filter(Archive.ar_timestamp > start_date)
            .filter(Archive.ar_timestamp <= end_date))

        if self.namespaces.data and len(self.namespaces.data) > 0:
            revisions = (
                revisions
                .join(Page)
                .filter(Page.page_namespace.in_(self.namespaces.data))
            )
            archives = (
                archives
                .filter(Archive.ar_namespace.in_(self.namespaces.data))
            )

        revisions = self.filter(revisions, user_ids, column=Revision.rev_user)
        archives = self.filter(archives, user_ids, column=Archive.ar_user)

        both = revisions
        if self.include_deleted.data:
            both = both.union_all(archives)
        both = both.subquery()

        if deduplicate:
            # Use a constant user id here to deduplicate only by page
            # A single result will be returned and assigned to user_id = ROLLUP_USER_ID
            both_grouped = (
                session.query(
                    label('user_id', literal_column(str(ROLLUP_USER_ID))), both.c.page_id
                )
                .distinct().subquery()
            )
        else:
            # Select distinct user_id-page_id pairs
            # to count edits by the same user on the same page as one
            both_grouped = (
                session.query(both.c.user_id, both.c.page_id)
                .distinct().subquery()
            )

        query = (
            session.query(both_grouped.c.user_id, func.count())
            .group_by(both_grouped.c.user_id)
        )

        # Format the output
        metric_results = {r[0]: {PagesEdited.id : r[1]} for r in query.all()}
        if user_ids is None:
            return metric_results
        elif deduplicate:
            ret = {}
            ret[ROLLUP_USER_ID] = metric_results.get(
                ROLLUP_USER_ID, self.default_result
            )
            return ret
        else:
            return {
                uid: metric_results.get(uid, self.default_result)
                for uid in user_ids
            }
