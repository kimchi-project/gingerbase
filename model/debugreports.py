#
# Project Ginger Base
#
# Copyright IBM Corp, 2015-2016
#
# Code derived from Project Kimchi
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
import glob
import logging
import os
import shutil
import subprocess
import time

from wok.asynctask import AsyncTask
from wok.exception import InvalidParameter
from wok.exception import NotFoundError
from wok.exception import OperationFailed
from wok.exception import WokException
from wok.model.tasks import TaskModel
from wok.plugins.gingerbase import config
from wok.utils import run_command
from wok.utils import wok_log


class DebugReportsModel(object):
    def __init__(self, **kargs):
        self.objstore = kargs['objstore']
        self.task = TaskModel(**kargs)

    def create(self, params):
        ident = params.get('name').strip()
        # Generate a name with time and millisec precision, if necessary
        if ident is None or ident == '':
            ident = 'report-' + str(int(time.time() * 1000))
        else:
            if ident in self.get_list():
                raise InvalidParameter('GGBDR0008E', {'name': ident})
        taskid = self._gen_debugreport_file(ident)
        return self.task.lookup(taskid)

    def get_list(self):
        path = config.get_debugreports_path()
        file_pattern = os.path.join(path, '*.*')
        file_lists = glob.glob(file_pattern)
        file_lists = [os.path.split(file)[1] for file in file_lists]
        name_lists = [file.split('.', 1)[0] for file in file_lists]

        return name_lists

    def _gen_debugreport_file(self, name):
        gen_cmd = self.get_system_report_tool()

        if gen_cmd is not None:
            return AsyncTask('/plugins/gingerbase/debugreports/%s' % name,
                             gen_cmd, name).id

        raise OperationFailed('GGBDR0002E')

    @staticmethod
    def debugreport_generate(cb, name):
        def log_error(e):
            wok_log = logging.getLogger('Model')
            wok_log.warning('Exception in generating debug file: %s', e)

        try:
            # Sosreport generation
            sosreport_file = sosreport_collection(name)
            md5_report_file = sosreport_file + '.md5'
            report_file_extension = '.' + sosreport_file.split('.', 1)[1]
            # If the platform is a system Z machine.
            path_debugreport = '/var/tmp/'
            dbginfo_report = None
            dbgreport_regex = path_debugreport + 'DBGINFO-' + \
                '[0-9][0-9][0-9][0-9]-' + '[0-9][0-9]-' + \
                '[0-9][0-9]-' + '[0-9][0-9]-' + '[0-9][0-9]-' + \
                '[0-9][0-9]-' + '*-' + '*.tgz'
            command = ['/usr/sbin/dbginfo.sh', '-d', path_debugreport]
            output, error, retcode = run_command(command)
            if retcode != 0:
                raise OperationFailed('GGBDR0009E',
                                      {'retcode': retcode, 'err': error})
            # Checking for dbginforeport file.
            if output.splitlines():
                dbginfo_report = glob.glob(dbgreport_regex)
            if len(dbginfo_report) == 0:
                raise OperationFailed('GGBDR0012E',
                                      {'retcode': retcode, 'err': error})
            dbginfo_reportfile = dbginfo_report[-1]
            final_tar_report_name = name + report_file_extension
            sosreport_tar = sosreport_file.split('/', 3)[3]
            dbginfo_tar = dbginfo_reportfile.split('/', 3)[3]
            msg = 'Compressing the sosreport and debug info files into ' \
                  'final report file'
            wok_log.info(msg)
            # Compressing the sosreport and dbginfo reports into one
            # tar file
            command = ['tar', '-cvzf', '%s' % final_tar_report_name,
                       '-C', path_debugreport, dbginfo_tar,
                       sosreport_tar]
            output, error, retcode = run_command(command)
            if retcode != 0:
                raise OperationFailed('GGBDR0010E',
                                      {'retcode': retcode,
                                       'error': error})
            path = config.get_debugreports_path()
            dbg_target = os.path.join(path,
                                      name + report_file_extension)
            # Moving final tar file to debugreports path
            msg = 'Moving final debug  report file "%s" to "%s"' % \
                  (final_tar_report_name, dbg_target)
            wok_log.info(msg)
            shutil.move(final_tar_report_name, dbg_target)
            # Deleting the sosreport md5 file
            delete_the_sosreport_md5_file(md5_report_file)
            # Deleting the dbginfo report file
            msg = 'Deleting the dbginfo file "%s" ' \
                  % dbginfo_reportfile
            wok_log.info(msg)
            os.remove(dbginfo_reportfile)
            # Deleting the sosreport file
            msg = 'Deleting the sosreport file "%s" ' % sosreport_file
            wok_log.info(msg)
            os.remove(sosreport_file)
            wok_log.info('The debug report file has been moved')
            cb('OK', True)
            return

        except WokException as e:
            log_error(e)
            raise

        except OSError as e:
            log_error(e)
            raise

        except Exception as e:
            # No need to call cb to update the task status here.
            # The task object will catch the exception raised here
            # and update the task status there
            log_error(e)
            raise OperationFailed('GGBDR0011E', {'name': name, 'err': e})

    @staticmethod
    def sosreport_generate(cb, name):
        def log_error(e):
            wok_log = logging.getLogger('Model')
            wok_log.warning('Exception in generating debug file: %s', e)
        try:
            # Sosreport collection
            sosreport_file = sosreport_collection(name)
            md5_report_file = sosreport_file + '.md5'
            report_file_extension = '.' + sosreport_file.split('.', 1)[1]
            path = config.get_debugreports_path()
            sosreport_target = os.path.join(path,
                                            name + report_file_extension)
            msg = 'Moving debug report file "%s" to "%s"' \
                  % (sosreport_file, sosreport_target)
            wok_log.info(msg)
            shutil.move(sosreport_file, sosreport_target)
            delete_the_sosreport_md5_file(md5_report_file)
            cb('OK', True)
            return

        except WokException as e:
            log_error(e)
            raise

        except OSError as e:
            log_error(e)
            raise

        except Exception as e:
            # No need to call cb to update the task status here.
            # The task object will catch the exception raised here
            # and update the task status there
            log_error(e)
            raise OperationFailed('GGBDR0005E', {'name': name, 'err': e})

    @staticmethod
    def get_system_report_tool():
        # Please add new possible debug report command here
        # and implement the report generating function
        # based on the new report command
        report_tools = ({'cmd': '/usr/sbin/dbginfo.sh --help',
                         'fn': DebugReportsModel.debugreport_generate},
                        {'cmd': 'sosreport --help',
                         'fn': DebugReportsModel.sosreport_generate},)

        # check if the command can be found by shell one by one
        for helper_tool in report_tools:
            try:
                retcode = subprocess.call(helper_tool['cmd'], shell=True,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE)
                if retcode == 0:
                    return helper_tool['fn']
            except Exception as e:
                wok_log.info('Exception running command: %s', e)

        return None


class DebugReportModel(object):
    def __init__(self, **kargs):
        pass

    def lookup(self, name):
        path = config.get_debugreports_path()
        file_pattern = os.path.join(path, name)
        file_pattern = file_pattern + '.*'
        try:
            file_target = glob.glob(file_pattern)[0]
        except IndexError:
            raise NotFoundError('GGBDR0001E', {'name': name})

        ctime = os.stat(file_target).st_mtime
        ctime = time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime(ctime))
        file_target = os.path.split(file_target)[-1]
        file_target = os.path.join('plugins/gingerbase/data/debugreports',
                                   file_target)
        return {'uri': file_target,
                'ctime': ctime}

    def update(self, name, params):
        path = config.get_debugreports_path()
        file_pattern = os.path.join(path, name + '.*')
        try:
            file_source = glob.glob(file_pattern)[0]
        except IndexError:
            raise NotFoundError('GGBDR0001E', {'name': name})

        f_name = os.path.basename(file_source).replace(name, params['name'], 1)
        file_target = os.path.join(path, f_name)
        if os.path.isfile(file_target):
            raise InvalidParameter('GGBDR0008E', {'name': params['name']})

        shutil.move(file_source, file_target)
        wok_log.info('%s renamed to %s' % (file_source, file_target))
        return params['name']

    def delete(self, name):
        path = config.get_debugreports_path()
        file_pattern = os.path.join(path, name + '.*')
        try:
            file_target = glob.glob(file_pattern)[0]
        except IndexError:
            raise NotFoundError('GGBDR0001E', {'name': name})

        os.remove(file_target)


class DebugReportContentModel(object):
    def __init__(self, **kargs):
        self._debugreport = DebugReportModel()

    def lookup(self, name):
        return self._debugreport.lookup(name)


def delete_the_sosreport_md5_file(md5_file):
    """
    Deleting md5 file and displaying the contents of the same.
    """
    msg = 'Deleting report md5 file: "%s"' % md5_file
    wok_log.info(msg)
    with open(md5_file) as f:
        md5 = f.read().strip()
        wok_log.info('Md5 file content: "%s"', md5)
    os.remove(md5_file)


def sosreport_collection(name):
    """
    Code for the collection of sosreport in the path
    /var/tmp as specified in the command.
    """
    path_sosreport = '/var/tmp/'
    sosreport_file = None
    if '_' in name:
        raise InvalidParameter('GGBDR0013E', {'name': name})
    command = ['sosreport', '--batch', '--name=%s' % name,
               '--tmp-dir=%s' % path_sosreport]
    output, error, retcode = run_command(command)
    if retcode != 0:
        raise OperationFailed('GGBDR0003E', {'name': name,
                                             'err': error})
    # Checking for sosreport file generation.
    if output.splitlines():
        sosreport_pattern = path_sosreport + 'sosreport-' \
            + name + '-' + '*.tar.xz'
        sosreport_file = glob.glob(sosreport_pattern)
    if len(sosreport_file) == 0:
        raise OperationFailed('GGBDR0004E', {'name': name,
                                             'err': retcode})
    return sosreport_file[0]
