from ..utils import thirty_days_ago, today
from sqlalchemy import func, case
from metric import Metric
from form_fields import CommaSeparatedIntegerListField, BetterDateTimeField
from wtforms.validators import Required
from sqlalchemy.sql.expression import label, between, and_, or_
from wtforms import BooleanField, IntegerField
from wikimetrics.models import Page, Revision, MediawikiUser
from sqlalchemy import Integer
import datetime
import calendar


__all__ = ['Survivors']


class Survivors(Metric):
    """
    This metric counts the survivors .
    
    The SQL query that inspired this metric was:
    
 SELECT revs.user_id AS revs_user_id,
        IF(revs.rev_count >= 1, 1, 0) AS survived,
        IF(revs.rev_count >= 1, 0, IF(unix_timestamp(now())
            < unix_timestamp(revs.user_registration) + 2595600, 1, 0)) AS censored

   FROM (SELECT user.user_id AS user_id,
                user.user_registration AS user_registration,
                coalesce(rev_count.rev_count, 0) AS rev_count
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
                        <survival> AND <survival + sunset>
                  GROUP BY user.user_id
                ) AS rev_count     ON user.user_id = rev_count.user_id
          WHERE user.user_id IN (<cohort>)
        ) AS revs
    """
    
    show_in_ui  = True
    id          = 'survival'
    label       = 'Survival'
    description = (
        'Compute whether editors "survived" by making n edits in the time period\
        starting at their registration + survival hours and ending at\
        their registration + survival hours + sunset hours'
    )
    
    number_of_edits       = IntegerField(default=1)
    survival_hours        = IntegerField(default=0)
    sunset_in_hours       = IntegerField(default=0)
    
    namespaces = CommaSeparatedIntegerListField(
        None,
        [Required()],
        default='0',
        description='0, 2, 4, etc.',
    )
    
    def debug_print(self, r, session, user_ids):
        s = ''
        for uid in user_ids:
            if uid:
                user_name = session \
                    .query(MediawikiUser.user_name) \
                    .filter(MediawikiUser.user_id == uid) \
                    .first()[0]
                s += '{0} ({1}) ===> [{2}] [{3}] \n'.format(
                    user_name, str(uid), str(r[uid]['survivor']), str(r[uid]['censored'])
                )
        print(s)
    
    def __call__(self, user_ids, session):
        """
        Parameters:
            user_ids    : list of mediawiki user ids to find edit for
            session     : sqlalchemy session open on a mediawiki database
        
        Returns:
            dictionary from user ids to the number of edit found.
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
            .filter(MediawikiUser.user_id.in_(user_ids)) \
            .filter(Page.page_namespace.in_(self.namespaces.data))
        
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
            .outerjoin(revisions, MediawikiUser.user_id == revisions.c.user_id) \
            .filter(MediawikiUser.user_id.in_(user_ids)) \
            .subquery()
        
        metric = session.query(
            revs.c.user_id,
            func.unix_timestamp(func.now()),
            func.IF(
                func.unix_timestamp(func.now()) <
                func.unix_timestamp(revs.c.user_registration) +
                (survival_hours + sunset_in_hours) * 3600,
                1, 0
            ),
            revs.c.rev_count,
            label('survived', func.IF(revs.c.rev_count >= number_of_edits, 1, 0)),
            label('censored', func.IF(
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
                'survivor': u.survived,
                'censored': u.censored,
            }
            for u in data
        }
        
        return {
            uid: metric_results.get(uid, {
                'survivor': None,
                'censored': None,
            })
            for uid in user_ids
        }
