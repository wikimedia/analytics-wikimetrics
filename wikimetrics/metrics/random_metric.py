class RandomMetric(object):
    def __call__(self, cohort):
        return {user:random.rand() for user in cohort}
