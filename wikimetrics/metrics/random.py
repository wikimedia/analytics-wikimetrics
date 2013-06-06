import random

class RandomMetric(object):
    def __call__(self, cohort):
        return {user:random.random() for user in cohort}
