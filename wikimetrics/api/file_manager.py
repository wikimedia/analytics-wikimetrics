import os
import os.path
import json
import shutil
import collections

from datetime import timedelta
from wikimetrics.exceptions import PublicReportIOError
from wikimetrics.utils import update_dict, parse_date_from_public_report_file, today
from wikimetrics.enums import Aggregation, TimeseriesChoices
# TODO ultils imports flask response -> fix

# Illegal filename characters
RESERVED_FILENAME_CHARACTERS = {' ', os.sep, ':', '<', '>', '"', '/', '\\', '|', '?', '*'}

# Filename used for coalesced report files
COALESCED_REPORT_FILE = 'full_report.json'


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
    
    def get_public_report_path(self, report_id, recurrent=False, create=False):
        """
        Parameters
           report_id : unique identifier for the report, a string
           recurrent : a boolean specifying whether the report is recurrent
           create : a boolean specifying if this method should create the returned
                    directory path on the file system.  This parameter is only
                    meaningful if recurrent == True

        Returns
           The path to a public report file if recurrent is False, otherwise
           the path to a recurrent public report directory
        """
        path_parts = [self.root_dir, 'static', 'public']

        if recurrent:
            path_parts.append(self.sanitize_path(str(report_id)))
            if create:
                self.ensure_dir(os.sep.join(path_parts))
        else:
            path_parts.append('{}.json'.format(self.sanitize_path(str(report_id))))

        return os.sep.join(path_parts)

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

    def sanitize_path(self, name_string):
        return ''.join(c if c not in RESERVED_FILENAME_CHARACTERS and ord(c) > 31 else
                       '_' for c in name_string)

    def create_file_name(self, name_string, date_object=None):
        """
        Create a string from a report name and optional datetime object suitable
        for use as a filename
        """
        result = self.sanitize_path(name_string)
        if date_object:
            result += '-' + self.sanitize_path(str(date_object))
        return result

    def ensure_dir(self, root, path=""):
        """
        Creates a new directory composed of root + os.sep + path, if the directory
        does not already exist, and automatically creates any specified parent
        directories in path which don't exist.
        """
        path = os.sep.join((root, path))
        if not os.path.exists(path):
            os.makedirs(path)

    def remove_recurrent_report(self, report_id):
        """
        Removes a series of recurrent, public reports from persistent storage

        Parameters:
            report_id : unique identifier for the report, a string
        """
        try:
            path = self.get_public_report_path(report_id, recurrent=True)

            if not os.path.isdir(path):
                msg = '"{0}" is not a scheduled report'.format(path)
                self.logger.exception(msg)
                raise PublicReportIOError(msg)

            shutil.rmtree(path)
        except IOError:
            msg = 'Could not remove concatenate public report {0} at "{1}"'.format(
                report_id, path)
            self.logger.exception(msg)
            raise PublicReportIOError(msg)

    def remove_old_report_files(self, report_id, days_ago=10):
        """
        Removes the individual (single-day) report files from the report folder
        that are older than 'days_ago'. The full report file will be left intact.
        """
        limit_day = today() - timedelta(days=days_ago)

        path = self.get_public_report_path(report_id, recurrent=True)
        if not os.path.isdir(path):
            msg = '"{0}" is not a scheduled report'.format(path)
            self.logger.exception(msg)
            raise PublicReportIOError(msg)

        for filename in os.listdir(path):
            if filename != COALESCED_REPORT_FILE:
                file_date = parse_date_from_public_report_file(filename)
                if file_date <= limit_day:
                    full_path = os.sep.join((path, filename))
                    self.remove_file(full_path)

    def coalesce_recurrent_reports(self, report_id):
        """
        Coalesces a series of recurrent, public reports into a single JSON
        object.  The coalesced object is a single dictionary mapping report
        END DATES to individual report objects.

        Parameters
            report_id : unique identifier for the report, a string

        Returns
            A JSON object containing the coalesced reports
        """
        try:
            coalesced_reports = {}
            path = self.get_public_report_path(report_id, recurrent=True)

            if not os.path.isdir(path):
                msg = '"{0}" is not a scheduled report'.format(path)
                self.logger.exception(msg)
                raise PublicReportIOError(msg)

            # Get a list of filenames with COALESCED_REPORT_FILE at 1st position,
            # so that new individual reports override the current full report.
            filenames = os.listdir(path)
            if COALESCED_REPORT_FILE in filenames:
                filenames.remove(COALESCED_REPORT_FILE)
                filenames.insert(0, COALESCED_REPORT_FILE)

            for f in filenames:
                full_path = os.sep.join((path, f))
                if os.path.isfile(full_path):
                    with open(full_path, 'r') as saved_report:
                        try:
                            data = json.load(saved_report)
                            _merge_run(coalesced_reports, data)

                        except KeyError, e:
                            msg = 'Key "{}" not in JSON file "{}"'.format(e, full_path)
                            self.logger.exception(msg)
                        except ValueError:
                            msg = 'Error parsing JSON file "{}"'.format(full_path)
                            self.logger.exception(msg)

            return coalesced_reports
        except IOError:
            msg = 'Could not concatenate public report {0}'.format(report_id)
            self.logger.exception(msg)
            raise PublicReportIOError(msg)


def _merge_run(coalesced, data):
    """
    Helper function, handles merging of new report results into an existing dictionary
    that represents the output of a recurrent report.  Correctly merges both timeseries
    and non-timeseries results into a timeseries-like format.

    Parameters
        coalesced   : the coalesced report to update, could be an empty dictionary
        data        : the json result of the new report
    """
    coalesced.setdefault('parameters', data['parameters'])
    coalesced.setdefault('result', {})

    timeseries = data['parameters'].get('Metric_timeseries', TimeseriesChoices.NONE)
    if timeseries == TimeseriesChoices.NONE:
        date = data['parameters']['Metric_end_date']
        for aggregate in data['result']:
            if aggregate == Aggregation.IND:
                for user in data['result'][aggregate]:
                    for submetric in data['result'][aggregate][user]:
                        t = type(data['result'][aggregate][user][submetric])
                        if t != dict:  # If it is not already a timeseries
                            # Shape the data so it all looks like timeseries
                            data['result'][aggregate][user][submetric] = {
                                date: data['result'][aggregate][user][submetric]
                            }
            else:
                for submetric in data['result'][aggregate]:
                    t = type(data['result'][aggregate][submetric])
                    if t != dict:  # If it is not already a timeseries
                        # Shape the data so it all looks like timeseries
                        data['result'][aggregate][submetric] = {
                            date: data['result'][aggregate][submetric]
                        }

    update_dict(coalesced['result'], data['result'])
