import random
from metric import Metric

class RandomMetric(Metric):
    def __call__(self, cohort):
        return {user:random.random() for user in cohort}
