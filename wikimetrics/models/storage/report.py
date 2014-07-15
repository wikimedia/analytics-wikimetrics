import celery
import json
from sqlalchemy import Column, Integer, String, DateTime, Boolean, func, ForeignKey
from sqlalchemy.orm import Session
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.sql.expression import and_
from sqlalchemy.exc import SQLAlchemyError
from wikimetrics.configurables import db, app
from wikimetrics.exceptions import UnauthorizedReportAccessError, PublicReportIOError


class ReportStore(db.WikimetricsBase):
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
    public = Column(Boolean)
    recurrent = Column(Boolean, default=False, nullable=False)
    recurrent_parent_id = Column(Integer, ForeignKey('report.id'))

    UniqueConstraint('recurrent_parent_id', 'created', name='uix_report')

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
                try:
                    existing_session.add(self)
                    existing_session.commit()
                finally:
                    existing_session.close()
            else:
                existing_session.commit()

    @staticmethod
    def update_reports(report_ids, owner_id, public=None, recurrent=None):
        """
        Updates reports in bulk, making sure they belong to an owner

        TODO: an Admin should be able to modify any report but it does not look we
        have an admin check (that kind of check should be cached)

        Parameters:
            report_ids  : list of ids of ReportStore objects to update
            owner_id    : the person purporting to own these reports
            public      : update all reports' public attribute to this, default is None
            recurrent   : update all reports' recurrent attribute to this, default is None

        Returns:
            True if the number of updated records matches the number of report_ids
            False otherwise
        """
        db_session = db.get_session()
        try:
            values = {}
            if public is not None:
                values['public'] = public
            if recurrent is not None:
                values['recurrent'] = recurrent
            update = db_session.execute(
                ReportStore.__table__.update()
                .values(**values)
                .where(and_(
                    ReportStore.id.in_(report_ids),
                    ReportStore.user_id == owner_id
                ))
            )
            db_session.commit()
        finally:
            db_session.close()

        if update and update.rowcount == len(report_ids):
            return True
        else:
            raise UnauthorizedReportAccessError(
                'Unauthorized access to report by {0}'.format(owner_id)
            )

    @staticmethod
    def make_report_public(report_id, owner_id, file_manager, data):
        """
        Parameters:
            report_id   : id of ReportStore to update
            owner_id    : the User purporting to own this report
            file_manager: PublicReportFileManager for file management
            data        : String, report data to write out to filepath
        """
        ReportStore.set_public_report_state(report_id, owner_id, file_manager,
                                            public=True, data=data)

    @staticmethod
    def make_report_private(report_id, owner_id, file_manager):
        """
        Parameters:
            report_id   : id of ReportStore to update
            owner_id    : the User purporting to own this report
            file_manager: PublicReportFileManager for file management
        """
        ReportStore.set_public_report_state(report_id, owner_id, file_manager,
                                            public=False)

    @staticmethod
    def set_public_report_state(report_id, owner_id, file_manager, public=True, data=''):
        """
        Internal method that sets a report public/private status.
        If we are making a report private that
        was public before will remove files from disk.

        If a new report is made public it will save report to disk.

        Validation that user can update this report has already happened before
        we reach this method.

        The UI calls this method on a per report basis
        but updates can be done for a set of reports.

        TODO: This method should not have http level code and
            should be part of an API,
            not be on the controller.
        TODO: We should not open & close a session here, I think session should be
            open/closed at the beginning/end of the request
            using flask request scoped functions

        Parameters:
            report_id   : id of ReportStore to update
            owner_id    : the User purporting to own this report
            public      : True | False if True data must be present
            data        : String, report data to write out to filepath
            file_manager: PublicReportFileManager to manage io interactions

        Returns:
            Nothing

        Throws:
            Exception if there are issues making the report public or private

        A private report is has public=False
        """
        # NOTE: update_reports checks ownership and raises an exception if needed
        ReportStore.update_reports([report_id], owner_id, public=public)

        # good no exception
        try:
            db_session = db.get_session()
            path = file_manager.get_public_report_path(report_id)
            if public:
                file_manager.write_data(path, data)

            else:
                file_manager.remove_file(path)

        except (PublicReportIOError, SQLAlchemyError) as e:
            app.logger.exception(str(e))
            # if there was an IO error rollback prior changes
            # this issues a new query as now our session scope and
            # transaction scope are now the same
            ReportStore.update_reports([report_id], owner_id, public=not public)
            raise e

        finally:
            db_session.close()

    def get_result_safely(self, result):
        if result and isinstance(result, dict) and self.result_key in result:
            return result[self.result_key]
        else:
            return {'failure': 'result not available'}

    def get_json_result(self, result):
        result = self.get_result_safely(result)
        return {
            'result': result,
            'parameters': self.pretty_parameters()
        }

    def pretty_parameters(self):
        """
        TODO add tests for this method
        its name implies that it's generic but is looking for specific input/output
        """
        raw = json.loads(self.parameters)
        pretty = {}
        pretty['Cohort Size'] = raw['cohort']['size']
        pretty['Cohort'] = raw['cohort']['name']
        pretty['Metric'] = raw['metric']['name']
        pretty['Created On'] = self.created

        for k in ('csrf_token', 'name', 'label'):
            raw['metric'].pop(k, None)

        for k, v in raw['metric'].items():
            pretty['Metric_' + k] = v

        return pretty

    def __repr__(self):
        return '<ReportStore("{0}")>'.format(self.id)
