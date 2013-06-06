__all__ = [
    'Metric',
]

class Metric(object):
    def __call__(self, cohort):
        return {user:None for user in cohort}
