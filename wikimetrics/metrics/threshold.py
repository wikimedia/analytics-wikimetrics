import datetime
import calendar
from sqlalchemy import func, case, Integer
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import label, between, and_, or_
from wtforms.validators import Required
from wtforms import BooleanField, IntegerField

from wikimetrics.models import Page, Revision, MediawikiUser
from wikimetrics.utils import thirty_days_ago, today, CENSORED
from wikimetrics.forms.fields import CommaSeparatedIntegerListField, BetterDateTimeField
from metric import Metric


class Threshold(Metric):
    """
    Threshold is a metric that determines whether an editor has performed >= n edits
    in a specified time window. It is used to measure early user activation.  It also
    computes the time it took a user to reach the threshold, if they did.
    Time to Threshold is also computed by this metric.  This is the number
    of hours that it took an editor to reach exactly n edits.  If the editor did not
    reach the threshold, None is returned.
    
    The SQL that inspired this metric was:
    
 SELECT user_id,
        IF(rev_timestamp is not null, 1, 0) as threshold,
        IF(rev_timestamp is not null,
            (unix_timestamp(rev_timestamp) - unix_timestamp(user_registration)) / 3600,
            null
        ) as time_to_threshold
   FROM (SELECT r1.rev_user,
                r1.rev_timestamp,
                COUNT(*) AS number
           FROM revision r1
                    INNER JOIN
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
    
    show_in_ui              = True
    id                      = 'threshold'
    time_to_threshold_id    = 'time_to_threshold'
    label                   = 'Threshold'
    description = (
        'Compute whether editors made <number_of_edits> from \
        <registration> to <registration> + <threshold_hours>.  \
        Also compute the time it took them to reach that threshold, in hours.'
    )
    default_result = {
        'threshold': None,
        'time_to_threshold': None,
        CENSORED: None,
    }
    
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
        
        threshold_hours = int(self.threshold_hours.data)
        threshold_secs  = threshold_hours * 3600
        number_of_edits = int(self.number_of_edits.data)
        
        Revision2 = aliased(Revision, name='r2')
        ordered_revisions = session \
            .query(
                Revision.rev_user,
                Revision.rev_timestamp,
                label('number', func.count()),
            ) \
            .join(MediawikiUser) \
            .join(Page) \
            .join(
                Revision2,
                and_(
                    Revision.rev_user == Revision2.rev_user,
                    Revision.rev_timestamp >= Revision2.rev_timestamp
                )
            ) \
            .group_by(Revision.rev_user) \
            .group_by(Revision.rev_timestamp) \
            .filter(Page.page_namespace.in_(self.namespaces.data)) \
            .filter(
                func.unix_timestamp(Revision.rev_timestamp) -
                func.unix_timestamp(MediawikiUser.user_registration) <= threshold_secs
            )
        
        o_r = self.filter(ordered_revisions, user_ids).subquery()
        
        metric = session.query(
            MediawikiUser.user_id,
            label(
                Threshold.id,
                func.IF(o_r.c.rev_timestamp != None, 1, 0)
            ),
            label(
                Threshold.time_to_threshold_id,
                func.IF(
                    o_r.c.rev_timestamp != None,
                    (func.unix_timestamp(o_r.c.rev_timestamp) -
                        func.unix_timestamp(MediawikiUser.user_registration)) / 3600,
                    None
                )
            ),
            label(CENSORED, func.IF(
                o_r.c.rev_timestamp != None,
                0,
                func.IF(
                    func.unix_timestamp(MediawikiUser.user_registration) + threshold_secs
                    >
                    func.unix_timestamp(func.now()),
                    1,
                    0
                )
            ))
        ) \
            .outerjoin(
                o_r,
                and_(
                    MediawikiUser.user_id == o_r.c.rev_user,
                    o_r.c.number == number_of_edits))

        metric = self.filter(metric, user_ids, MediawikiUser.user_id)
        
        return {
            u.user_id: {
                Threshold.id                    : u.threshold,
                Threshold.time_to_threshold_id  : u.time_to_threshold,
                CENSORED                        : u.censored,
            }
            for u in metric.all()
        }
