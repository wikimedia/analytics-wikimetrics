from wtforms import BooleanField, IntegerField
from wikimetrics.metrics import Threshold


__all__ = ['Survival']


class Survival(Threshold):
    """
    Survival is a metric that determines whether an editor has performed a certain
    activity at least n times in a specified time window. It is used to measure early
    user activation (when t is measured from account creation) or
    during a certain window of interest
    (for example in an A/B test or a usability test for an editing gadget/feature)
    
    The SQL query that inspired this metric was:
    
 SELECT revs.user_id AS revs_user_id,
        IF(revs.rev_count >= 1, 1, 0) AS survived,
        IF(revs.rev_count >= 1, 0, IF(unix_timestamp(now())
            < unix_timestamp(revs.user_registration) + 2595600, 1, 0)) AS censored

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
                    AND page.page_namespace IN (0)
                    AND unix_timestamp(revision.rev_timestamp) -
                        unix_timestamp(user.user_registration)
                            BETWEEN
                        <survival_hours> AND <now>
                  GROUP BY user.user_id
                ) AS rev_counts     ON user.user_id = rev_count.user_id
          WHERE user.user_id IN (<cohort>)
        ) AS revs
    """
    id = 'survived'
    label = 'Survival'
    description = (
        'Compute whether editors "survived" by making <number_of_edits> from \
        <registration> + <survival_hours> to \
        <registration> + <survival_hours> + <sunset_in_hours>. \
        If sunset_in_hours is 0, look for edits from \
        <registration> + <survival_hours> to <today>.'
    )
    sunset_in_hours       = IntegerField(default=0)
