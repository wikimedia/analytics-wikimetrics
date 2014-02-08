import os
import os.path
from wikimetrics.exceptions import PublicReportIOError
# TODO ultils imports flask response -> fix
from wikimetrics.utils import ensure_dir


class PublicReportFileManager():
    """
    Encapsulates access to filesystem and application level
    operations related to public reports.
    
    Stateless, safer as a singleton or application scoped object.
    There is an instance of this class that already lives on
    flask application globals.
    
    You can access this global via g:
    from flask import g
    file_manager = g.file_manager
    
    Please do not add static methods as we want to be able to
    mock this class easily
    
    """
    def __init__(self, logger, root_dir):
        """
        Parameters
           logger :
           root_dir: absolute path under which we want to create reports
        
        """
        self.logger = logger
        self.root_dir = root_dir
    
    def get_public_report_path(self, report_id):
        """
        Careful:
            If directory doesn't exist it will try to create it!
            This is only meaningful in local setup, in any other setup puppet
            should have create this directory
        Parameters
           report_id : unique identifier for the report, a string
        
        """
        report_dir = os.sep.join(('static', 'public'))
        ensure_dir(self.root_dir, report_dir)
        return os.sep.join((self.root_dir, report_dir, '{}.json'.format(report_id)))
    
    def write_data(self, file_path, data):
        """
        Writes data to a given path
        
        Parameters
           file_path : The path to which we are writing the public report
           data: String content to write
        
        Returns
            PublicReportIOError
            if an IOError was raised when creating the public report
        """
        try:
            with open(file_path, 'w') as saved_report:
                saved_report.write(data)
        except IOError:
            msg = 'Could not create public report at: {0}'.format(file_path)
            self.logger.exception(msg)
            raise PublicReportIOError(msg)
    
    def remove_file(self, file_path):
        """
        
        Parameters
           file_path : The path to the file to be deleted
        
        Returns
            PublicReportIOError
            if an IOError was raised when deleting the public report
        """
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            else:
                raise PublicReportIOError('Could not remove public report at: '
                                          '{0} as it does not exist'.format(file_path))
        
        except IOError:
            msg = 'Could not remove public report at: {0}'.format(file_path)
            self.logger.exception(msg)
            raise PublicReportIOError(msg)
