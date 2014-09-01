import datetime
import calendar
from sqlalchemy import func, case, Integer
from sqlalchemy.sql.expression import label, between, and_, or_
from wtforms.validators import Required
from wtforms import BooleanField, IntegerField

from wikimetrics.utils import thirty_days_ago, today, CENSORED
from wikimetrics.models import Page, Revision, MediawikiUser
from wikimetrics.forms.fields import CommaSeparatedIntegerListField, BetterDateTimeField
from metric import Metric


class Survival(Metric):
    """
    Survival is a metric that determines whether an editor has performed >= n edits
    in a specified time window. It is used to measure early user activation.
    
    The SQL query that inspired this metric was:
    
 SELECT revs.user_id AS revs_user_id,
        IF(revs.rev_count >= <number_of_edits>, 1, 0)
            AS survived,
        IF(revs.rev_count >= <number_of_edits>, 0, IF(unix_timestamp(now())
            < unix_timestamp(revs.user_registration) + <survival_hours>, 1, 0))
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
                            BETWEEN
                        <survival_hours> AND <now>
                  GROUP BY user.user_id
                ) AS rev_counts     ON user.user_id = rev_count.user_id
          WHERE user.user_id IN (<cohort>)
        ) AS revs
    """
    
    show_in_ui  = True
    id          = 'survived'
    label       = 'Survival'
    category    = 'Retention'
    description = (
        'Compute whether editors "survived" by making <number_of_edits> from \
        <registration> + <survival_hours> to \
        <registration> + <survival_hours> + <sunset_in_hours>. \
        If sunset_in_hours is 0, look for edits from \
        <registration> + <survival_hours> to <today>.'
    )
    default_result = {
        'survived': None,
        CENSORED: None,
    }
    
    number_of_edits = IntegerField(default=1)
    survival_hours  = IntegerField(default=0)
    sunset_in_hours = IntegerField(default=0)
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
                'survived': 1 for True, 0 for False,
                'censored': 1 for True, 0 for False
            }
        """
        
        survival_hours = int(self.survival_hours.data)
        sunset_in_hours = int(self.sunset_in_hours.data)
        number_of_edits = int(self.number_of_edits.data)
        
        revisions = session \
            .query(
                MediawikiUser.user_id,
                label('rev_count', func.count())
            ) \
            .join(Revision) \
            .join(Page) \
            .group_by(MediawikiUser.user_id) \
            .filter(Page.page_namespace.in_(self.namespaces.data))
        
        revisions = self.filter(revisions, user_ids, column=MediawikiUser.user_id)

        # sunset_in_hours is zero, so we use the first case [T+t,today]
        if sunset_in_hours == 0:
            revisions = revisions.filter(
                between(
                    func.unix_timestamp(Revision.rev_timestamp) -
                    func.unix_timestamp(MediawikiUser.user_registration)
                    ,
                    (survival_hours * 3600)
                    ,
                    func.unix_timestamp(func.now()) + 86400
                )
            )
        # otherwise use the sunset_in_hours [T+t,T+t+s]
        else:
            revisions = revisions.filter(
                between(
                    func.unix_timestamp(Revision.rev_timestamp) -
                    func.unix_timestamp(MediawikiUser.user_registration)
                    ,
                    (survival_hours * 3600)
                    ,
                    ((survival_hours + sunset_in_hours) * 3600)
                )
            )
        
        revisions = revisions.subquery()
        revs = session.query(
            MediawikiUser.user_id,
            MediawikiUser.user_registration,
            label(
                'rev_count',
                func.coalesce(revisions.c.rev_count, 0)
            )
        ) \
            .outerjoin(revisions, MediawikiUser.user_id == revisions.c.user_id)

        revs = self.filter(revs, user_ids, MediawikiUser.user_id).subquery()
        
        metric = session.query(
            revs.c.user_id,
            label(Survival.id, func.IF(revs.c.rev_count >= number_of_edits, 1, 0)),
            label(CENSORED, func.IF(
                revs.c.rev_count >= number_of_edits,
                0,
                func.IF(
                    func.unix_timestamp(func.now()) <
                    func.unix_timestamp(revs.c.user_registration) +
                    (survival_hours + sunset_in_hours) * 3600,
                    1, 0
                )
            ))
        )
        
        data = metric.all()
        
        metric_results = {
            u.user_id: {
                Survival.id : u.survived,
                CENSORED    : u.censored,
            }
            for u in data
        }
        
        r = {
            uid: metric_results.get(uid, self.default_result)
            for uid in user_ids or metric_results.keys()
        }
        
        #self.debug_print(r, session, user_ids)
        return r
