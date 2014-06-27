from inspect import getmembers


class CohortProperty(object):
    """
    Instances of this are useful as properties of Cohort instances.
    If a Cohort declares a property X, of type CohortProperty, its __init__ will try to
    do this: self.X = data.X and raise an exception if it can't
    """


class Cohort(object):
    """
    Base class for all cohort types.  Objects created by a member of this class hierarchy
    are just meant to carry data.  They do not have any logic or dependency on storage.
    Properties are declaratively defined as instances of CohortProperty, then their value
    is copied from data passed to the generic constructor.
    """

    def __init__(self, data, size):
        """
        Goes through the passed in data parameter and validates that it contains all the
        expected properties this Cohort describes, matching by name.
        Parameters:
            data    : an object that contains one property for each CohortProperty
                      defined on self.__class__, matched by name
            size    : the number of users in this cohort, 0 if this is a cohort with a
                      dynamic membership
        """
        self.size = size
        for k, p in getmembers(self.__class__, lambda p: type(p) == CohortProperty):
            try:
                setattr(self, k, getattr(data, k))
            except:
                raise

    id                  = CohortProperty()
    name                = CohortProperty()
    description         = CohortProperty()
    default_project     = CohortProperty()
    created             = CohortProperty()
    enabled             = CohortProperty()
    public              = CohortProperty()
    has_validation_info = False
