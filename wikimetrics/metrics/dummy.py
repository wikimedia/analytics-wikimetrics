import random
from metric import Metric
import logging

__all__ = ['RandomMetric']

logger = logging.getLogger(__name__)


class RandomMetric(Metric):
    """
    This class is defined for testing purposes.
    An instance of the class is callable and will return a random number for every
    user passed in.
    """
    def __call__(self, user_ids, session):
        """
        Parameters:
            user_ids    : list of user ids to return random numbers for
            session     : sqlalchemy session open on a mediawiki database (not required here)
        
        Returns:
            dictionary from user ids to the number of edit reverts found.
        """
        return {user: random.random() for user in user_ids}
