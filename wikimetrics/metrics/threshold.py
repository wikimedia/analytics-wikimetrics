from wikimetrics.metrics import Metric
import datetime
import calendar
from sqlalchemy import func, case, Integer
from sqlalchemy.sql.expression import label, between, and_, or_

from wikimetrics.models import Page, Revision, MediawikiUser
from wikimetrics.utils import thirty_days_ago, today, CENSORED
from form_fields import CommaSeparatedIntegerListField, BetterDateTimeField
from wtforms.validators import Required
from wtforms import BooleanField, IntegerField


__all__ = ['Threshold']


class Threshold(Metric):
    """
    Threshold is a metric that determines whether an editor has performed >= n edits
    in a specified time window. It is used to measure early user activation.  It also
    computes the time it took a user to reach the threshold, if they did.
    
    The SQL query that inspired this metric was:
    
 SELECT revs.user_id AS revs_user_id,
        IF(revs.rev_count >= <number_of_edits>, 1, 0)
            AS threshold,
        IF(revs.rev_count >= <number_of_edits>, 0, IF(unix_timestamp(now())
            < unix_timestamp(revs.user_registration) + <threshold_hours>, 1, 0))
            AS censored

   FROM (SELECT user.user_id AS user_id,
                user.user_registration AS user_registration,
                coalesce(rev_counts.rev_count, 0) AS rev_count
           FROM user
                        LEFT OUTER JOIN
                (SELECT user.user_id AS user_id,
                        count(*) as rev_count
                   FROM user
                                INNER JOIN
                        revision    ON user.user_id = revision.rev_user
                                INNER JOIN
                        page        ON page.page_id = revision.rev_page
                  WHERE user.user_id IN (<cohort>)
                    AND page.page_namespace IN (<namespaces>)
                    AND unix_timestamp(revision.rev_timestamp) -
                        unix_timestamp(user.user_registration)
                            <= <threshold_hours>
                  GROUP BY user.user_id
                ) AS rev_counts     ON user.user_id = rev_count.user_id
          WHERE user.user_id IN (<cohort>)
        ) AS revs

    And the Time to Threshold sub-metric is also computed by this metric.  This is the number
    of hours that it took an editor to reach exactly n edits.  If the editor did not
    reach the threshold, None is returned.  The inspiration SQL for this is:
    
 SELECT user_id,
        IF(rev_timestamp is not null,
            (unix_timestamp(rev_timestamp) - unix_timestamp(user_registration)) / 3600,
            null
        ) as time_to_threshold
   FROM (SELECT r1.rev_user,
                r1.rev_timestamp,
                COUNT(*) AS number
           FROM revision r1
                  JOIN
                revision r2  ON r1.rev_user = r2.rev_user
                             AND r1.rev_timestamp >= r2.rev_timestamp
          WHERE user.user_id IN (<cohort>)
            AND page.page_namespace IN (<namespaces>)
            AND unix_timestamp(revision.rev_timestamp) -
                unix_timestamp(user.user_registration)
                    <= <threshold_hours>
          GROUP BY
                r1.rev_user,
                r1.rev_timestamp
        ) ordered_revisions
            LEFT JOIN
        user            on user.user_id = ordered_revisions.rev_user
                        and ordered_revisions.number = <number_of_edits>
  WHERE user_id IN (<cohort>)
    """
    
    show_in_ui  = True
    id          = 'threshold'
    label       = 'Threshold'
    description = (
        'Compute whether editors made <number_of_edits> from \
        <registration> to <registration> + <threshold_hours>.  \
        Also compute the time it took them to reach that threshold, in hours.'
    )
    
    number_of_edits = IntegerField(default=1)
    threshold_hours = IntegerField(default=24)
    namespaces      = CommaSeparatedIntegerListField(
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
            dictionary from user ids to a dictionary of the form:
            {
                'threshold': 1 for True, 0 for False,
                'time_to_threshold': number in hours or None,
                'censored': 1 for True, 0 for False
            }
        """
        return 'Not Implemented'
