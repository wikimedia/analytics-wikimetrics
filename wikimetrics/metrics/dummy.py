import random
from wtforms import IntegerField
from metric import Metric


__all__ = ['RandomMetric']


class RandomMetric(Metric):
    """
    This class is defined for testing purposes.
    An instance of the class is callable and will return a random number for every
    user passed in.
    """
    
    show_in_ui  = False
    id          = 'random'
    label       = 'Random'
    description = 'test metric, compute random numbers for all users in your cohort(s)'
    
    test_field = IntegerField(default=1000)
    
    def __call__(self, user_ids, session):
        """
        Parameters:
            user_ids    : list of user ids to return random numbers for
            session     : sqlalchemy session open on a mediawiki database
        
        Returns:
            dictionary from user ids to the number of edit reverts found.
        """
        return {user: random.random() + self.test_field.data for user in user_ids}
