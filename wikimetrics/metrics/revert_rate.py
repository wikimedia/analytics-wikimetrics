from metric import Metric

__all__ = [
    'RevertRate',
]

''' The SQL Query to find reverts a cohort:

 select r.rev_user, r.count(*)
   from revision r
  where r.rev_timestamp between [start] and [end]
    and r.rev_user in ([cohort's user list or maybe a join to a temp])
    and exists (
         select *
           from revision r1
                    inner join
                revision r2     on r2.rev_sha1 = r1.rev_sha1
          where r1.rev_page = r.rev_page
            and r2.rev_page = r.rev_page
            and r1.rev_timestamp between [start] and r.rev_timestamp
            and r2.rev_timestamp between r.rev_timestamp and [end]
        )
  group by rev_user

'''
class RevertRate(Metric):
    def __call__(self, cohort):
        return {user:None for user in cohort}
