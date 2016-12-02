#
# Project Ginger Base
#
# Copyright IBM Corp, 2016
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

import fileinput
import os
import platform
import re
import shutil

from wok.exception import OperationFailed, InvalidParameter, InvalidOperation
from wok.utils import run_command, wok_log
from wok.plugins.gingerbase.lscpu import LsCpu

ARCH = platform.machine()

ZIPL = '/etc/zipl.conf'
PARAMETERS = "parameters="
NOSMT = "nosmt"
SMT_TWO = "smt=2"
SMT_ONE = "smt=1"
SMT = "smt"


class SmtModel(object):
    _confirm_timeout = 10.0

    def __init__(self, **kargs):
        pass

    def lookup(self, name):
        if ARCH.startswith('s390x'):
            return self.get_smt_status_s390x()
        else:
            raise OperationFailed("GINSMT0013E", {'name': ARCH})

    def get_smt_status_s390x(self):
        """
        Method to fetch the smt status for s390x architecture..
        Returns:
        info : dictionary of SMT status with persisted ('/etc/zipl.conf')
        and current info ('/proc/cmdline').
        """
        try:
            if self.check_smt_support():
                info = dict()
                info['current_smt_settings'] = dict()
                info['persisted_smt_settings'] = dict()
                info['current_smt_settings'] = \
                    self.get_current_settings_s390x()
                info['persisted_smt_settings'] = \
                    self.get_persistent_settings_s390x()
                return info
            else:
                raise OperationFailed("GINSMT0006E")
        except OperationFailed:
            raise
        except Exception:
            raise InvalidOperation("GINSMT0010E")

    def get_current_settings_s390x(self):
        """
        Method to return current SMT settings ('/proc/cmdline')
        for s390x architecture.
        Returns:
        current_smt_settings: dictionary {status, value}
        """
        command = ['cat', '/proc/cmdline']
        threads_per_core = LsCpu().get_threads_per_core()
        output, error, retcode = run_command(command)
        if retcode != 0:
            raise OperationFailed("GINSMT003E", {'error': error})
        elif (SMT_TWO in output or SMT not in output):
            status = "enabled"
            value = 2
        elif SMT_ONE in output and threads_per_core < 2:
            status = "enabled"
            value = 1
        elif NOSMT in output and threads_per_core < 2:
            status = "disabled"
            value = NOSMT
        else:
            raise InvalidOperation("GINSMT0001E")
        current_smt_settings = {'status': status,
                                'smt': value}
        return current_smt_settings

    def get_persistent_settings_s390x(self):
        """
        Method to return persisted ('/etc/zipl.conf') SMT settings for
        s390x architecture.
        Returns:
        persisted_smt_settings: dictionary {status, value}.
        """
        if os.path.isfile(str(ZIPL)):
            command = ['cat', '/etc/zipl.conf']
            output, error, retcode = run_command(command)
            if retcode != 0:
                raise OperationFailed("GINSMT003E", {'error': error})
            elif SMT_TWO in output or SMT not in output:
                status = "enabled"
                value = 2
            elif SMT_ONE in output:
                status = "enabled"
                value = SMT_ONE.split("=")[1]
            elif NOSMT in output:
                status = "disabled"
                value = NOSMT
            else:
                raise OperationFailed("GINSMT0011E")
            persisted_smt_settings = {'status': status,
                                      'smt': value}
            return persisted_smt_settings
        raise OperationFailed("GINSMT0012E")

    def write_zipl_file(self, name, smt_val):
        """
        Method to write and update the  zipl file for
        s390x architecture.
        """
        try:
            smt_input = "smt" + "=" + smt_val
            var = ' ' + smt_input + '"'
            for line in fileinput.FileInput(ZIPL, inplace=1):
                match = re.search(r'smt\S\d*', line)
                if PARAMETERS in line:
                    if NOSMT in line:
                        regex = "\s*nosmt"
                        line = re.sub(regex, "", line)
                        line = line.replace(line, line[:-2] + var + "\n")
                    if match:
                        if smt_input not in line:
                            regex = '\s*smt\S\d*'
                            line = re.sub(regex, "", line)
                            line = line.replace(line, line[:-2] + var + "\n")
                    else:
                        if "parameters=" in line and smt_input not in line:
                            line = line.replace(line, line[:-2] + var + "\n")
                print line,
        except Exception:
            raise OperationFailed("GINSMT0002E")

    def enable(self, name, smt_val):
        """
        Enables the SMT.
        """
        if ARCH.startswith('s390x'):
            self.enable_smt_s390x(name, smt_val)
        else:
            raise InvalidOperation("GINSMT0007E", {'name': 'enable'})

    def disable(self, name):
        """
        Disables the SMT.
        """
        if ARCH.startswith('s390x'):
            self.disable_smt_s390x(name)
        else:
            raise InvalidOperation("GINSMT0007E", {'name': 'disable'})

    def enable_smt_s390x(self, name, smt_val):
        """
        Method to enable the SMT for s390x architecture.
        """
        value = smt_val.isdigit()
        if value:
            if os.path.isfile(str(ZIPL)):
                backup_file = ZIPL + "_bak"
                shutil.copy(ZIPL, backup_file)
                self.write_zipl_file(name, smt_val)
                self.load_smt_s390x(backup_file)
                wok_log.info("Successfully enabled SMT settings.")
            else:
                raise OperationFailed("GINSMT0012E")
        else:
            raise InvalidParameter("GINSMT0004E")

    def disable_smt_s390x(self, name):
        """
        Method to disable SMT for s390x architecture
        """
        try:
            if os.path.isfile(str(ZIPL)):
                backup_file = ZIPL + "_bak"
                shutil.copy(ZIPL, backup_file)
                var = ' ' + NOSMT + '"'
                for line in fileinput.FileInput(ZIPL, inplace=1):
                    if "parameters=" in line and NOSMT not in line:
                        regex = '\s*smt\S\d*'
                        line = re.sub(regex, "", line)
                        line = line.replace(line, line[:-2] + var + "\n")
                    print line,
                self.load_smt_s390x(backup_file)
                wok_log.info("Successfully disabled SMT settings.")
            else:
                raise OperationFailed("GINSMT0012E")
        except OperationFailed:
            raise
        except Exception:
            raise InvalidOperation("GINSMT0005E")

    def recover_ziplfile(self, ziplfile, backupfile):
        """
        Method to  recover the /etc/zipl.conf file in case of failure on
        s390x architecture.
        """
        if os.path.isfile(backupfile):
            shutil.copy(backupfile, ziplfile)
            os.remove(backupfile)

    def load_smt_s390x(self, backup):
        """
        Method to execute the changes done in zipl file
         for s390x architecture.
        """
        command = ['zipl']
        output, error, retcode = run_command(command)
        if retcode != 0:
            self.recover_ziplfile(ZIPL, backup)
            raise OperationFailed("GINSMT0008E", {'error': error})
        wok_log.info("Successfully applied SMT settings.")

    def check_smt_support(self):
        """
        Method to check SMT supported or not.
        Return:
         True
        """
        try:
            cp_count = 0
            un_count = 0
            ifl_count = 0
            command = ['cat', '/proc/sysinfo']
            output, error, retcode = run_command(command)
            if retcode != 0:
                raise OperationFailed("GINSMT0003E", {'error': error})
            regex = "(LPAR Name:)\s+(\w+)"
            match = re.search(regex, output)
            lpar_name = match.group(2)
            command = \
                ['hyptop', '-b', '-n', '1', '-w', 'sys', '-s', '%s'
                 % lpar_name]
            output, error, retcode = run_command(command)
            if retcode != 0:
                raise OperationFailed("GINSMT0009E", {'error': error})
            output = output.split('\n')
            regex = "\w+\s*(IFL)\s*(\d*[.]\d*\s*)*\S+\s*\S*"
            cpregex = "\w+\s*(CP)\s*(\d*[.]\d*\s*)*\S+\s*\S*"
            unregex = "\w+\s*(UN)\s*(\d*[.]\d*\s*)*\S+\s*\S*"
            for each in output:
                if re.match(cpregex, each):
                    cp_count += 1
                if re.match(unregex, each):
                    un_count += 1
                if re.match(regex, each):
                    ifl_count += 1
            if un_count == 0 and cp_count == 0 and ifl_count > 0:
                return True
            else:
                return False
        except Exception:
            raise OperationFailed("GINSMT0006E")
