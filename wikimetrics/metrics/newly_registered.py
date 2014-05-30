from wikimetrics.metrics import Metric

from wikimetrics.models.mediawiki import Logging
from wikimetrics.utils import thirty_days_ago, today
from form_fields import BetterDateTimeField


class NewlyRegistered(Metric):
    """
    A newly registered user is a previously unregistered user creating a username
    for the first time on a Wikimedia project.

    The SQL query that inspired this metric was:

 SELECT log_user AS user_id
   FROM enwiki.logging
        /* exclude proxy registrations */
  WHERE log_type = 'newusers'
        /* only include self-created users, exclude attached and proxy-registered users */
    AND log_action = 'create'
    AND log_timestamp BETWEEN @start_date AND @end_date;
    """

    show_in_ui  = True
    id          = 'newly_registered'
    label       = 'Newly Registered'
    description = (
        'A newly registered user is a previously unregistered user creating a username \
        for the first time on a Wikimedia project.'
    )

    start_date  = BetterDateTimeField(default=thirty_days_ago)
    end_date    = BetterDateTimeField(default=today)

    def __call__(self, user_ids, session):
        """
        Parameters:
            user_ids    : list of mediawiki user ids to investigate
            session     : sqlalchemy session open on a mediawiki database

        Returns:
            dictionary from user ids to a dictionary of the form:
            {
                'newly_registered': 1 for True, 0 for False
            }
            If no user_ids are specified, only {'newly_registered': 1} will be returned
            for those user ids which satisfy the metric
        """

        start_date = self.start_date.data
        end_date = self.end_date.data

        query = session.query(Logging.log_user) \
            .filter(Logging.log_type == 'newusers') \
            .filter(Logging.log_action == 'create') \
            .filter(Logging.log_timestamp > start_date)\
            .filter(Logging.log_timestamp <= end_date)

        metric = self.filter(query, user_ids, column=Logging.log_user)
        data = metric.all()
        print data

        metric_results = {r[0]: {NewlyRegistered.id : 1} for r in data}

        if user_ids is None:
            return metric_results
        else:
            return {
                uid: metric_results.get(uid, {NewlyRegistered.id : 0})
                for uid in user_ids
            }
