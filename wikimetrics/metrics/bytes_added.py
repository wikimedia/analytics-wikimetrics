import Metric

__all__ = [
    'BytesAdded',
]

''' The SQL Query to find bytes added for a cohort:

 select sum(cast(r.rev_len as signed) - cast(coalesce(previous_r.rev_len, 0) as signed)) as net_sum
        ,sum(abs(cast(r.rev_len as signed) - cast(coalesce(previous_r.rev_len, 0) as signed))) as abs_sum
        ,sum(case
            when cast(r.rev_len as signed) - cast(coalesce(previous_r.rev_len, 0) as signed) > 0
            then cast(r.rev_len as signed) - cast(coalesce(previous_r.rev_len, 0) as signed)
            else 0
        end) as pos_sum
        ,sum(case
            when cast(r.rev_len as signed) - cast(coalesce(previous_r.rev_len, 0) as signed) < 0
            then abs(cast(r.rev_len as signed) - cast(coalesce(previous_r.rev_len, 0) as signed))
            else 0
        end) as neg_sum
        ,count(*) as edits
   from revision r
            inner join
        page p              on p.page_id = r.rev_page
            left join
        revision previous_r on previous_r.rev_id = r.rev_parent_id
  where p.page_namespace = 0
    and r.rev_timestamp between [start] and [end]
    and r.rev_user in <<cohorts>>

'''
class BytesAdded(Metric):
    def __call__(self, cohort):
        return {user:None for user in cohort}
