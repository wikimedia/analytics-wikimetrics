from ..utils import thirty_days_ago, today
from sqlalchemy import func, case
from metric import Metric
from form_fields import CommaSeparatedIntegerListField, BetterDateTimeField
from wtforms.validators import Required
from sqlalchemy.sql.expression import label, between, and_
from wtforms import BooleanField, IntegerField
from wikimetrics.models import Page, Revision, MediawikiUser
import datetime
import calendar

from pprint import pprint
import sys


__all__ = ['Survivors']


class Survivors(Metric):
    """
    This class counts the survivors over a period of time.

    This sql query was used as a starting point for the sqlalchemy query:

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

    def debug_print(self, q, session, user_ids):
        r = dict(q.all())
        s = ""
        for uid in user_ids:
            if uid:
                user_name = session \
                    .query(MediawikiUser.user_name) \
                    .filter(MediawikiUser.user_id == uid) \
                    .first()[0]
                val_survivor = r[uid] if uid in r else 0
                s += user_name + " (" + str(uid) + ") ===> " + str(val_survivor) + "\n"
        print s

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

        partial_query = session \
            .query(Revision.rev_user, label("rev_count", func.count(Revision.rev_id))) \
            .join(MediawikiUser) \
            .join(Page) \
            .filter(Page.page_namespace.in_(self.namespaces.data)) \
            .filter(Revision.rev_user.in_(user_ids))

       # sunset is zero, so we use the first case [T+t,today]
        if sunset == 0:
            q = partial_query.filter(
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
        else:
            q = partial_query.filter(
                between(
                    func.unix_timestamp(Revision.rev_timestamp)
                    ,
                    func.unix_timestamp(MediawikiUser.user_registration) +
                    (survival_hours * 3600)
                    ,
                    func.unix_timestamp(MediawikiUser.user_registration) +
                    ((survival_hours + sunset) * 3600))
            )
        q = q.group_by(Revision.rev_user) \
             .subquery()
        
        f = session.query(q.c.rev_user,
                          case([(q.c.rev_count >= number_of_edits, 1)], else_=0))

        #self.debug_print(f, session, user_ids)

        survivors = dict(f.all())
        return {
            user_id: {'survivors': survivors.get(user_id, 0)}
            for user_id in user_ids
        }
