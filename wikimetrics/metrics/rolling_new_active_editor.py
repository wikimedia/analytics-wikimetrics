from sqlalchemy import func
from sqlalchemy.sql.expression import label, between
from datetime import timedelta
from wtforms import IntegerField

from wikimetrics.forms.fields import BetterDateTimeField
from wikimetrics.utils import today
from wikimetrics.models.mediawiki import Revision, Archive, Logging
from metric import Metric


class RollingNewActiveEditor(Metric):
    """
    This sql query was used as a starting point for the sqlalchemy query:

    SET @n = <<edits threshold, default 5>>;
    SET @u = <<activity unit in days, default 30>>;
    SET @T = <<end date passed in, or each date between start and end if timeseries>>;

     SELECT user_id
       FROM (/* Get revisions to content pages that are still visible */
             SELECT user_id,
                    SUM(rev_id IS NOT NULL) AS revisions
               FROM User
                        INNER JOIN
                    Logging     ON log_user = user_id
                        LEFT JOIN
                    Revision    ON rev_user = user_id
              WHERE log_type = 'newusers'
                AND log_action = 'create'
                AND user_registration BETWEEN [@T - @u days] AND @T
                AND rev_timestamp BETWEEN [@T - @u days] AND @T
              GROUP BY user_id

              UNION ALL

             /* Get revisions to content pages that have been archived */
             SELECT user_id,
                    /* Note that ar_rev_id is sometimes set to NULL :( */
                    SUM(ar_id IS NOT NULL) AS revisions
               FROM User
                        INNER JOIN
                    Logging     ON log_user = user_id
                        LEFT JOIN
                    Archive     ON ar_user = user_id
              WHERE log_type = 'newusers'
                AND log_action = 'create'
                AND user_registration BETWEEN [@T - @u days] AND @T
                AND ar_timestamp BETWEEN [@T - @u days] AND @T
              GROUP BY user_id
            ) AS user_content_revision_count
      GROUP BY user_id
     HAVING SUM(revisions) >= @n;
    """

    show_in_ui  = True
    id          = 'rolling_new_active_editor'
    label       = 'Rolling New Active Editor'
    category    = 'Acquisition'
    description = (
        'Compute the number of newly registered users who complete <<n>> edits to pages'
        ' in any namespace of a Wikimedia project between <<end date>> minus <<u>> days'
        ' and <<end date>>'
    )
    default_result  = {
        'rolling_new_active_editor': 0,
    }

    number_of_edits = IntegerField(default=5)
    rolling_days    = IntegerField(default=30)
    end_date        = BetterDateTimeField(
        label='As Of Date',
        default=today,
        description='Newly Registered users making Number Of Edits within '
                    'Rolling Days of this date'
    )

    def __call__(self, user_ids, session):
        """
        Parameters:
            user_ids    : list of mediawiki user ids to restrict computation to
            session     : sqlalchemy session open on a mediawiki database

        Returns:
            {
                user id: 1 if they're a rolling new active editor, 0 otherwise
                for all cohort users, or all users that have edits in the time period
            }
        """
        number_of_edits = int(self.number_of_edits.data)
        rolling_days = int(self.rolling_days.data)
        end_date = self.end_date.data
        start_date = end_date - timedelta(days=rolling_days)

        newly_registered = session.query(Logging.log_user) \
            .filter(Logging.log_type == 'newusers') \
            .filter(Logging.log_action == 'create') \
            .filter(between(Logging.log_timestamp, start_date, end_date))

        filtered_new = self.filter(
            newly_registered, user_ids, column=Logging.log_user
        ).subquery()

        rev_user = label('user_id', Revision.rev_user)
        ar_user = label('user_id', Archive.ar_user)
        count = label('count', func.count())

        revisions = session.query(rev_user, count)\
            .filter(between(Revision.rev_timestamp, start_date, end_date))\
            .filter(Revision.rev_user.in_(filtered_new))\
            .group_by(Revision.rev_user)

        archived = session.query(ar_user, count)\
            .filter(between(Archive.ar_timestamp, start_date, end_date))\
            .filter(Archive.ar_user.in_(filtered_new))\
            .group_by(Archive.ar_user)

        new_edits = revisions.union_all(archived).subquery()
        new_edits_by_user = session.query(
            new_edits.c.user_id,
            func.IF(func.SUM(new_edits.c.count) >= number_of_edits, 1, 0)
        )\
            .group_by(new_edits.c.user_id)

        metric_results = {r[0]: {self.id : r[1]} for r in new_edits_by_user.all()}

        if user_ids is None:
            return metric_results
        else:
            return {
                uid: metric_results.get(uid, self.default_result)
                for uid in user_ids
            }
