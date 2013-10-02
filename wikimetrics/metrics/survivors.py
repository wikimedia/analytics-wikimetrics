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
    This class counts the survivors over a period of time.
    """
    
    show_in_ui  = True
    id          = 'survivors'
    label       = 'Survivors'
    description = (
        'Compute the number of pages created by each \
         editor in a time interval'
    )
    
    number_of_edits       = IntegerField(default=1)
    survival_hours        = IntegerField(default=0)
    sunset                = IntegerField(default=0)
    
    namespaces = CommaSeparatedIntegerListField(
        None,
        [Required()],
        default='0',
        description='0, 2, 4, etc.',
    )
    
    def debug_print(self, r, session, user_ids):
        s = ""
        for uid in user_ids:
            if uid:
                user_name = session \
                    .query(MediawikiUser.user_name) \
                    .filter(MediawikiUser.user_id == uid) \
                    .first()[0]
                s += '{0} ({1}) ===> [{2}] [{3}] \n'.format(
                    user_name, str(uid), str(r[uid]["survivor"]), str(r[uid]["censored"])
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
        sunset = int(self.sunset.data)
        number_of_edits = int(self.number_of_edits.data)
        
        revisions = session \
            .query(MediawikiUser.user_id) \
            .join(Revision) \
            .join(Page) \
            .filter(MediawikiUser.user_id.in_(user_ids)) \
            .filter(Page.page_namespace.in_(self.namespaces.data))
        
        # sunset is zero, so we use the first case [T+t,today]
        # TODO: censored is 0
        if sunset == 0:
            revisions = revisions.filter(
                between(
                    func.unix_timestamp(Revision.rev_timestamp)
                    ,
                    func.unix_timestamp(MediawikiUser.user_registration) +
                    (survival_hours * 3600)
                    ,
                    func.unix_timestamp(func.now()) + 86400
                )
            )
        # otherwise use the sunset [T+t,T+t+s]
        # TODO: censored is 0 if now() >= T+t+s
        else:
            revisions = revisions.filter(
                between(
                    func.unix_timestamp(Revision.rev_timestamp)
                    ,
                    func.unix_timestamp(MediawikiUser.user_registration) +
                    (survival_hours * 3600)
                    ,
                    func.unix_timestamp(MediawikiUser.user_registration) +
                    ((survival_hours + sunset) * 3600)
                )
            )
        
        revisions = revisions.subquery()
        revs = session.query(
            MediawikiUser.user_id,
            MediawikiUser.user_registration,
            label(
                "rev_count",
                func.sum(func.IF(revisions.c.user_id != None, 1, 0))
            )
        ) \
            .outerjoin(revisions, MediawikiUser.user_id == revisions.c.user_id) \
            .group_by(MediawikiUser.user_id) \
            .subquery()
        
        metric = session.query(
            revs.c.user_id,
            func.unix_timestamp(func.now()),
            func.IF(
                func.unix_timestamp(func.now()) <
                func.unix_timestamp(revs.c.user_registration) +
                (survival_hours + sunset) * 3600,
                1, 0
            ),
            revs.c.rev_count,
            label("survived", func.IF(revs.c.rev_count >= number_of_edits, 1, 0)),
            label("censored", func.IF(
                revs.c.rev_count >= number_of_edits,
                0,
                func.IF(
                    func.unix_timestamp(func.now()) <
                    func.unix_timestamp(revs.c.user_registration) +
                    (survival_hours + sunset) * 3600,
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
