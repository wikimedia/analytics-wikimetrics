from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import Session
from wikimetrics.configurables import db, app
from celery.exceptions import SoftTimeLimitExceeded
from datetime import datetime


class TaskErrorStore(db.WikimetricsBase):
    """
    Stores the information about a task failure.

    To avoid saturating the database with tons of duplicated records
    for the same task failing again and again, all errors pertaining
    to a same task will be collapsed into one record.

    The 'count' column holds how many times an error has happened.
    The error message and traceback and also the timestamp take the
    value of the last occurrence for debugging purposes.
    """
    __tablename__ = 'task_error'

    task_type = Column(Integer, primary_key=True, autoincrement=False)
    task_id = Column(Integer, ForeignKey('report.id'),
                     primary_key=True, autoincrement=False)
    timestamp = Column(DateTime, default=func.now())
    message = Column(String(100))
    traceback = Column(String(3000))
    count = Column(Integer)

    @staticmethod
    def add(task_type, task_id, message, traceback):
        db_session = db.get_session()
        existing = TaskErrorStore.get(db_session, task_type, task_id)
        if existing:
            TaskErrorStore.update(db_session, existing, message, traceback)
        else:
            TaskErrorStore.create(db_session, task_type, task_id, message, traceback)
        db_session.close()

    @staticmethod
    def get(db_session, task_type, task_id):
        task_error = (
            db_session
            .query(TaskErrorStore)
            .filter(TaskErrorStore.task_type == task_type)
            .filter(TaskErrorStore.task_id == task_id)
            .all()
        )
        if len(task_error) > 0:
            return task_error[0]
        else:
            return None

    @staticmethod
    def create(db_session, task_type, task_id, message, traceback):
        task_error = TaskErrorStore(
            task_type=task_type,
            task_id=task_id,
            timestamp=datetime.now(),
            message=message,
            traceback=traceback,
            count=1
        )
        db_session.add(task_error)
        db_session.commit()

    @staticmethod
    def update(db_session, task_error, message, traceback):
        task_error.message = message
        task_error.traceback = traceback
        task_error.timestamp = datetime.now()
        task_error.count += 1
        db_session.commit()

    def __repr__(self):
        return '<TaskErrorStore("{0}", "{1}")>'.format(self.task_type, self.task_id)
