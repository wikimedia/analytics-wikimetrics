__all__ = [
    'Metric',
]

class Metric(object):
    def __call__(self, user_ids, project):
        return {user:None for user in user_ids}
