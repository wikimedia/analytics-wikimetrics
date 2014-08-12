import itertools
from operator import itemgetter
from sqlalchemy import Column, Integer, Boolean, DateTime, String, func

from wikimetrics.exceptions import Unauthorized
from wikimetrics.configurables import db
from wikiuser import WikiUserStore
from cohort_wikiuser import CohortWikiUserStore
from user import UserStore


class CohortStore(db.WikimetricsBase):
    """
    This class represents a list of users along with the project
    on which their username exists.  Using sqlalchemy.declarative
    It maps to the cohort table  which keeps metadata about the cohort,
    however it is also home to a variety of convenience functions
    for interacting with the actual list of users in that cohort.

    Importantly, there is no guarantee that a cohort consist of users
    from a single project.  To get the set of all users associated with
    a single project within a cohort use CohortStore.group_by_project.
    """

    __tablename__ = 'cohort'

    class_name              = Column(String(50), default='FixedCohort', nullable=False)
    id                      = Column(Integer, primary_key=True)
    name                    = Column(String(50))
    description             = Column(String(254))
    default_project         = Column(String(50))
    created                 = Column(DateTime, default=func.now())
    changed                 = Column(DateTime)
    enabled                 = Column(Boolean)
    public                  = Column(Boolean, default=False)
    validated               = Column(Boolean, default=False)
    validate_as_user_ids    = Column(Boolean, default=True)
    validation_queue_key    = Column(String(50))

    def __repr__(self):
        return '<CohortStore("{0}")>'.format(self.id)

    # TODO: that weird bug that makes "None" show up in metric results
    # starts with iterating CohortStore here
    def __iter__(self):
        """
        Returns list of user_ids to filter by to obtain data for just for this cohort.
        TODO: remove this method, it only makes sense for single-project cohorts and
              Cohort display that will be removed soon.

        """
        db_session = db.get_session()
        wikiusers = self.filter_wikiuser_query(
            db_session.query(WikiUserStore.mediawiki_userid)
        ).all()
        return (r.mediawiki_userid for r in wikiusers)

    def __len__(self):
        """
        NOTE: this can be different than the length of the result of __iter__,
        because database changes might occur in between calls.  So any code that
        depends on that not being the case *may* fail in unexpected and wild ways.

        Returns:
            the number of users in this cohort
        """
        db_session = db.get_session()
        return db_session.query(func.count(CohortWikiUserStore.id)) \
            .join(WikiUserStore) \
            .filter(CohortWikiUserStore.cohort_id == self.id) \
            .filter(WikiUserStore.valid) \
            .one()[0]

    def group_by_project(self):
        """
        mimics the interface of itertools.groupby, with the
        exception that the grouped items are simply user_ids
        rather than complete user records

        Returns:
            iterable of tuples of the form:
                (project, <iterable_of_usernames>)

        this is useful for turning a project-heterogenous cohort
        into a set of project-homogenous cohorts, which can be
        analyzed using a single database connection
        """
        db_session = db.get_session()
        user_id_projects = self.filter_wikiuser_query(
            db_session.query(WikiUserStore.mediawiki_userid, WikiUserStore.project)
        ).order_by(WikiUserStore.project).all()

        if not len(user_id_projects):
            return [(self.default_project, None)]

        groups = itertools.groupby(user_id_projects, key=itemgetter(1))

        return (
            (project or self.default_project, (r[0] for r in users))
            for project, users in groups
        )

    def filter_wikiuser_query(self, wikiusers_query):
        """
        Parameters:
            wikiusers_query : a sqlalchemy query object asking for one or more
                                properties of WikiUser

        Return:
            the query object passed in, filtered and joined to the
            appropriate tables, and restricted to this cohort
        """
        return wikiusers_query\
            .join(CohortWikiUserStore)\
            .join(CohortStore)\
            .filter(CohortStore.id == self.id)\
            .filter(CohortStore.validated)\
            .filter(WikiUserStore.valid)
