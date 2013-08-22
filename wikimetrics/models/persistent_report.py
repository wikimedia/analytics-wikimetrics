import celery
from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from sqlalchemy.orm import Session
from wikimetrics.configurables import db


__all__ = ['PersistentReport']


class PersistentReport(db.WikimetricsBase):
    """
    Stores each report node that runs in a report node tree to the database.
    Stores the necessary information to fetch the results from Celery as
    well as to re-run the node.
    """
    __tablename__ = 'report'
    
    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=func.now())
    user_id = Column(Integer)
    queue_result_key = Column(String(50))
    result_key = Column(String(50))
    status = Column(String(50))
    name = Column(String(2000))
    show_in_ui = Column(Boolean)
    parameters = Column(String(4000))
    
    def update_status(self):
        # if we don't have the result key leave as is
        if self.queue_result_key and self.status not in (celery.states.READY_STATES):
            # TODO: inline import.  Can't import up above because of circular reference
            from wikimetrics.models.report_nodes import Report
            celery_task = Report.task.AsyncResult(self.queue_result_key)
            self.status = celery_task.status
            existing_session = Session.object_session(self)
            if not existing_session:
                existing_session = db.get_session()
                existing_session.add(self)
            existing_session.commit()
