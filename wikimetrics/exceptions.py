class Unauthorized(Exception):
    """
    Different exception type to separate "unauthorized" errors from the rest
    """
    pass


class UnauthorizedReportAccessError(Exception):
    """
    Thrown when a user is trying to access a report that
    does not belong to him    """
    pass
        

class PublicReportIOError(Exception):
    """
    Thrown when we could not create or delete a public report in the filesystem
    
    """
    pass


class DatabaseError(Exception):
    """
    Thrown when database calls don't return an expected result.
    """
    pass


class InvalidCohort(Exception):
    """
    Thrown when invalid cohorts are retrieved from the database for reporting
    """
    pass
