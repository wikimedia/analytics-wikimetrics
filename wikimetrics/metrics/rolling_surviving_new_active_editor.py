from sqlalchemy import func
from sqlalchemy.sql.expression import label, between, and_
from datetime import timedelta
from wtforms import IntegerField

from wikimetrics.forms.fields import BetterDateTimeField
from wikimetrics.utils import today
from wikimetrics.models.mediawiki import Revision, Archive, Logging, MediawikiUserGroups
from metric import Metric


class RollingSurvivingNewActiveEditor(Metric):
    """
    This sql query was used as a starting point for the sqlalchemy query:

SET @n = <<edits threshold, default 5>>;
SET @u = <<activity unit in days, default 30>>;
SET @T = <<end date passed in, or each date between start and end if timeseries>>;

 SELECT user_id
   FROM (/* Get revisions to content pages that are still visible */
         SELECT user_id,
                SUM(rev_id IS NOT NULL and rev_timestamp <= [@T - @u days]) AS revisions1
                SUM(rev_id IS NOT NULL and rev_timestamp > [@T - @u days]) AS revisions2
           FROM User
                    INNER JOIN
                Logging     ON log_user = user_id
                    LEFT JOIN
                Revision    ON rev_user = user_id
          WHERE log_type = 'newusers'
            AND log_action = 'create'
            AND user_registration BETWEEN [@T - 2*@u days] AND [@T - @u days]
            AND rev_timestamp BETWEEN [@T - 2*@u days] AND @T
          GROUP BY user_id

          UNION ALL

         /* Get revisions to content pages that have been archived */
         SELECT user_id,
                /* Note that ar_rev_id is sometimes set to NULL :( */
                SUM(ar_id IS NOT NULL and ar_timestamp <= [@T - @u days]) AS revisions1
                SUM(ar_id IS NOT NULL and ar_timestamp > [@T - @u days]) AS revisions2
           FROM User
                    INNER JOIN
                Logging     ON log_user = user_id
                    LEFT JOIN
                Archive     ON ar_user = user_id
          WHERE log_type = 'newusers'
            AND log_action = 'create'
            AND user_registration BETWEEN [@T - 2*@u days] AND [@T - @u days]
            AND ar_timestamp BETWEEN [@T - 2*@u days] AND @T
          GROUP BY user_id
        ) AS user_content_revision_count
  GROUP BY user_id
 HAVING SUM(revisions1) >= @n
    AND SUM(revisions2) >= @n

    NOTE: updated to exclude bots as identified by:

 SELECT ug_user
   FROM user_groups
  WHERE ug_group = 'bot'
    """

    show_in_ui  = True
    id          = 'rolling_surviving_new_active_editor'
    label       = 'Rolling Surviving New Active Editor'
    category    = 'Community'
    description = (
        'Compute the number of users newly registered within <<end date>> minus <<u>> * 2'
        ' days who complete <<n>> edits to pages in any namespace of a Wikimedia project'
        ' two times.  Once between <<end date>> minus <<u>> days and <<end date>>.  Then'
        ' between <<end date>> minus <<u*2>> days and <<end date>> minus <<u>> days.'
    )
    default_result  = {
        'rolling_surviving_new_active_editor': 0,
    }

    number_of_edits = IntegerField(default=5)
    rolling_days    = IntegerField(default=30)
    end_date        = BetterDateTimeField(
        label='As Of Date',
        default=today,
        description='Newly Registered users making Number Of Edits within '
                    'Rolling Days * 2 of this date, and again another Number '
                    'Of Edits within Rolling Days of this date'
    )

    def __call__(self, user_ids, session):
        """
        Parameters:
            user_ids    : list of mediawiki user ids to restrict computation to
            session     : sqlalchemy session open on a mediawiki database

        Returns:
            {
                user id: 1 if they're a rolling surviving new active editor, 0 otherwise
                for all cohort users, or all users that have edits in the time period
            }
        """
        number_of_edits = int(self.number_of_edits.data)
        rolling_days = int(self.rolling_days.data)
        end_date = self.end_date.data
        mid_date = end_date - timedelta(days=rolling_days)
        start_date = end_date - timedelta(days=rolling_days * 2)

        newly_registered = session.query(Logging.log_user) \
            .filter(Logging.log_type == 'newusers') \
            .filter(Logging.log_action == 'create') \
            .filter(between(Logging.log_timestamp, start_date, mid_date))

        # subquery to select only the users registered between start and mid date
        filtered_new = self.filter(
            newly_registered, user_ids, column=Logging.log_user
        ).subquery()

        rev_user = label('user_id', Revision.rev_user)
        ar_user = label('user_id', Archive.ar_user)
        # count edits between start and mid date, for Revision
        rev_count_one = _get_count('count_one', Revision.rev_timestamp <= mid_date)
        # count edits between start and mid date, for Archive
        ar_count_one = _get_count('count_one', Archive.ar_timestamp <= mid_date)
        # count edits between mid and end date, for Revision
        rev_count_two = _get_count('count_two', Revision.rev_timestamp > mid_date)
        # count edits between mid and end date, for Archive
        ar_count_two = _get_count('count_two', Archive.ar_timestamp > mid_date)

        # get both counts by user for Revision
        revisions = session.query(rev_user, rev_count_one, rev_count_two)\
            .filter(between(Revision.rev_timestamp, start_date, end_date))\
            .filter(Revision.rev_user.in_(filtered_new))\
            .group_by(Revision.rev_user)

        # get both counts by user for Archive
        archived = session.query(ar_user, ar_count_one, ar_count_two)\
            .filter(between(Archive.ar_timestamp, start_date, end_date))\
            .filter(Archive.ar_user.in_(filtered_new))\
            .group_by(Archive.ar_user)

        bot_user_ids = session.query(MediawikiUserGroups.ug_user)\
            .filter(MediawikiUserGroups.ug_group == 'bot')\
            .subquery()

        # For each user, with both counts from both tables,
        #   sum the count_one values together, check it's >= number_of_edits
        #   sum the count_two values together, check it's >= number_of_edits
        new_edits = revisions.union_all(archived).subquery()
        new_edits_by_user = session.query(new_edits.c.user_id)\
            .filter(new_edits.c.user_id.notin_(bot_user_ids))\
            .group_by(new_edits.c.user_id)\
            .having(and_(
                func.SUM(new_edits.c.count_one) >= number_of_edits,
                func.SUM(new_edits.c.count_two) >= number_of_edits,
            ))

        metric_results = {r[0]: {self.id : 1} for r in new_edits_by_user.all()}

        if user_ids is None:
            return metric_results
        else:
            return {
                uid: metric_results.get(uid, self.default_result)
                for uid in user_ids
            }


def _get_count(text, if_clause):
    """helper to create query below"""
    return label(text, func.SUM(func.IF(if_clause, 1, 0)))
