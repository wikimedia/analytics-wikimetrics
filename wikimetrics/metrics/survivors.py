from ..utils import thirty_days_ago, today
from sqlalchemy import func
from metric import Metric
from form_fields import CommaSeparatedIntegerListField, BetterDateTimeField
from wtforms.validators import Required
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
    
    start_date            = BetterDateTimeField(default=thirty_days_ago)
    end_date              = BetterDateTimeField(default=today)
    survival_days         = IntegerField(default=0)
    use_registration_date = BooleanField(default=False)
    
    namespaces = CommaSeparatedIntegerListField(
        None,
        [Required()],
        default='0',
        description='0, 2, 4, etc.',
    )

    def convert_dates_to_timestamps(self):
        
        start_date = None
        end_date = None

        if type(self.start_date.data) == str:
            start_date = calendar.timegm(
                datetime.datetime.strptime(self.start_date.data, "%Y-%m-%d").timetuple())
        elif type(self.start_date.data) == datetime.date:
            start_date = calendar.timegm(self.start_date.data.timetuple())
        else:
            raise Exception("Problems with start_date")

        if type(self.end_date.data) == str:
            end_date = calendar.timegm(
                datetime.datetime.strptime(self.end_date.data, "%Y-%m-%d").timetuple())
        elif type(self.end_date.data) == datetime.date:
            end_date = calendar.timegm(self.end_date.data.timetuple())
        else:
            raise Exception("Problems with end_date")

        return start_date, end_date

    def __call__(self, user_ids, session):
        """
        Parameters:
            user_ids    : list of mediawiki user ids to find edit for
            session     : sqlalchemy session open on a mediawiki database
        
        Returns:
            dictionary from user ids to the number of edit found.
        """

        use_registration_date = self.use_registration_date.data
        survival_days = int(self.survival_days.data)

        start_date, end_date = self.convert_dates_to_timestamps()

        #print "use_registration_date=", use_registration_date

        #start_date = self.start_date
        #end_date = self.end_date

        #if session.bind.name == 'mysql':

        one_day_seconds = 3600 * 12

        survivors_by_namespace = None

        if use_registration_date:
            if survival_days > 0:
                print "\n\n[DBG] Case 1\n\n"
                # survival_days YES ; registration YES

                q = session \
                    .query(Revision.rev_user) \
                    .join(MediawikiUser) \
                    .join(Page) \
                    .filter(Page.page_namespace.in_(self.namespaces.data)) \
                    .filter(func.strftime("%s", Revision.rev_timestamp) -
                            func.strftime("%s", MediawikiUser.user_registration) >=
                            survival_days * one_day_seconds) \
                    .group_by(Revision.rev_user)

                survivors_by_namespace = [x[0] for x in q.all()]
            else:
                # survival_days NO ; registration YES
                #print "\n\n[DBG] Case 2\n\n"
                #print "end_date=", end_date
                q = session \
                    .query(Revision.rev_user) \
                    .join(MediawikiUser) \
                    .join(Page) \
                    .filter(Page.page_namespace.in_(self.namespaces.data)) \
                    .filter(func.strftime("%s", Revision.rev_timestamp) - end_date >= 0) \
                    .group_by(Revision.rev_user)

                survivors_by_namespace = [x[0] for x in q.all()]
        else:
            if survival_days:
                print "\n\n[DBG] Case 3\n\n"
                # survival_days YES ; registration NO
                q = session \
                    .query(Revision.rev_user) \
                    .join(MediawikiUser) \
                    .join(Page) \
                    .filter(Page.page_namespace.in_(self.namespaces.data)) \
                    .filter(func.strftime("%s", Revision.rev_timestamp) - start_date >=
                            (survival_days * one_day_seconds)) \
                    .group_by(Revision.rev_user)

                survivors_by_namespace = [x[0] for x in q.all()]

            else:
                print "\n\n[DBG] Case 4\n\n"
                # survival_days NO ; registration NO
                q = session \
                    .query(Revision.rev_user, "1") \
                    .join(MediawikiUser) \
                    .join(Page) \
                    .filter(Page.page_namespace.in_(self.namespaces.data)) \
                    .filter(func.strftime("%s", Revision.rev_timestamp) - end_date >= 0) \
                    .group_by(Revision.rev_user)

                survivors_by_namespace = [x[0] for x in q.all()]

        retval = {}

        pprint(survivors_by_namespace)
        for user_id in user_ids:
            if user_id in survivors_by_namespace:
                retval[user_id] = {'survivors' : True}
            else:
                retval[user_id] = {'survivors' : False}

        return retval
