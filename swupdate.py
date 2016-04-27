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

import fcntl
import os
import signal
import subprocess
import time
from configobj import ConfigObj, ConfigObjError
from psutil import pid_exists, process_iter

from wok.basemodel import Singleton
from wok.exception import NotFoundError, OperationFailed
from wok.utils import run_command, wok_log

from wok.plugins.gingerbase.config import gingerBaseLock
from wok.plugins.gingerbase.yumparser import get_dnf_package_info
from wok.plugins.gingerbase.yumparser import get_yum_package_info
from wok.plugins.gingerbase.yumparser import get_yum_packages_list_update


class SoftwareUpdate(object):
    __metaclass__ = Singleton

    """
    Class to represent and operate with OS software update.
    """
    def __init__(self):
        # Get the distro of host machine and creates an object related to
        # correct package management system
        try:
            __import__('dnf')
            wok_log.info("Loading DnfUpdate features.")
            self._pkg_mnger = DnfUpdate()
        except ImportError:
            try:
                __import__('yum')
                wok_log.info("Loading YumUpdate features.")
                self._pkg_mnger = YumUpdate()
            except ImportError:
                try:
                    __import__('apt')
                    wok_log.info("Loading AptUpdate features.")
                    self._pkg_mnger = AptUpdate()
                except ImportError:
                    zypper_help = ["zypper", "--help"]
                    (stdout, stderr, returncode) = run_command(zypper_help)
                    if returncode == 0:
                        wok_log.info("Loading ZypperUpdate features.")
                        self._pkg_mnger = ZypperUpdate()
                    else:
                        raise Exception("There is no compatible package "
                                        "manager for this system.")

    def getUpdates(self):
        """
        Return a list of packages eligigle to be updated in the system.
        """
        return [pkg for pkg in self._pkg_mnger.getPackagesList()]

    def getUpdate(self, name):
        """
        Return a dictionary with all info from a given package name.
        """
        package = self._pkg_mnger.getPackageInfo(name)
        if not package:
            raise NotFoundError('GGBPKGUPD0002E', {'name': name})
        return package

    def getNumOfUpdates(self):
        """
        Return the number of packages to be updated.
        """
        return len(self.getUpdates())

    def preUpdate(self):
        """
        Make adjustments before executing the command in
        a child process.
        """
        os.setsid()
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

    def tailUpdateLogs(self, cb, params):
        """
        When the package manager is already running (started outside gingerbase
        or if wokd is restarted) we can only know what's happening by reading
        the logfiles. This method acts like a 'tail -f' on the default package
        manager logfile. If the logfile is not found, a simple '*' is
        displayed to track progress. This will be until the process finishes.
        """
        if not self._pkg_mnger.isRunning():
            return

        fd = None
        try:
            fd = os.open(self._pkg_mnger.logfile, os.O_RDONLY)

        # cannot open logfile, print something to let users know that the
        # system is being upgrading until the package manager finishes its
        # job
        except (TypeError, OSError):
            msgs = []
            while self._pkg_mnger.isRunning():
                msgs.append('*')
                cb(''.join(msgs))
                time.sleep(1)
            msgs.append('\n')
            cb(''.join(msgs), True)
            return

        # go to the end of logfile and starts reading, if nothing is read or
        # a pattern is not found in the message just wait and retry until
        # the package manager finishes
        os.lseek(fd, 0, os.SEEK_END)
        msgs = []
        progress = []
        while True:
            read = os.read(fd, 1024)
            if not read:
                if not self._pkg_mnger.isRunning():
                    break

                if not msgs:
                    progress.append('*')
                    cb(''.join(progress))

                time.sleep(1)
                continue

            msgs.append(read)
            cb(''.join(msgs))

        os.close(fd)
        return cb(''.join(msgs), True)

    def doUpdate(self, cb, params):
        """
        Execute the update
        """
        # reset messages
        cb('')

        if params is not None:
            cmd = self._pkg_mnger.update_cmd['specific'] + params
        else:
            cmd = self._pkg_mnger.update_cmd['all']

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                preexec_fn=self.preUpdate)
        msgs = []
        while proc.poll() is None:
            msgs.append(proc.stdout.readline())
            cb(''.join(msgs))
            time.sleep(0.5)

        # read the final output lines
        msgs.extend(proc.stdout.readlines())

        retcode = proc.poll()
        if retcode == 0:
            return cb(''.join(msgs), True)

        msgs.extend(proc.stderr.readlines())
        return cb(''.join(msgs), False)


class YumUpdate(object):
    """
    Class to represent and operate with YUM software update system.
    It's loaded only on those systems listed at YUM_DISTROS and loads necessary
    modules in runtime.
    """
    def __init__(self):
        self.update_cmd = dict.fromkeys(['all', 'specific'],
                                        ["yum", "-y", "update"])
        self.logfile = self._get_output_log()

    def _get_output_log(self):
        """
        Return the logfile path
        """
        yumcfg = None
        try:
            yumcfg = ConfigObj('/etc/yum.conf')

        except ConfigObjError:
            return None

        if 'main' in yumcfg and 'logfile' in yumcfg['main']:
            return yumcfg['main']['logfile']

        return None

    def getPackagesList(self):
        """
        Return a list of packages eligible to be updated by Yum.
        """
        if self.isRunning():
            raise OperationFailed('GGBPKGUPD0005E')

        pkgs = []
        try:
            gingerBaseLock.acquire()
            pkgs = get_yum_packages_list_update()
        except Exception, e:
            raise OperationFailed('GGBPKGUPD0003E', {'err': str(e)})
        finally:
            gingerBaseLock.release()
        return pkgs

    def getPackageInfo(self, pkg_name):
        """
        Get package information. The return is a dictionary containg the
        information about a package, in the format:

        package = {'package_name': <string>,
                   'version': <string>,
                   'arch': <string>,
                   'repository': <string>,
                   'depends': <list>
                  }
        """
        if self.isRunning():
            raise OperationFailed('GGBPKGUPD0005E')

        package = {}
        try:
            gingerBaseLock.acquire()
            package = get_yum_package_info(pkg_name)
        except Exception, e:
            raise NotFoundError('GGBPKGUPD0003E', {'err': str(e)})
        finally:
            gingerBaseLock.release()
        return package

    def isRunning(self):
        """
        Return True whether the YUM package manager is already running or
        False otherwise.
        """
        try:
            with open('/var/run/yum.pid', 'r') as pidfile:
                pid = int(pidfile.read().rstrip('\n'))

        # cannot find pidfile, assumes yum is not running
        except (IOError, ValueError):
            return False

        # the pidfile exists and it lives in process table
        if pid_exists(pid):
            return True
        return False


class DnfUpdate(YumUpdate):
    """
    Class to represent and operate with DNF software update system.
    It's loaded only on those systems listed at DNF_DISTROS and loads necessary
    modules in runtime.
    """
    def __init__(self):
        self._pkgs = {}
        self.update_cmd = dict.fromkeys(['all', 'specific'],
                                        ["dnf", "-y", "update"])
        self.logfile = '/var/log/dnf.log'

    def getPackageInfo(self, pkg_name):
        """
        Get package information. The return is a dictionary containg the
        information about a package, in the format:

        package = {'package_name': <string>,
                   'version': <string>,
                   'arch': <string>,
                   'repository': <string>,
                   'depends': <list>
                  }
        """
        if self.isRunning():
            raise OperationFailed('GGBPKGUPD0005E')

        package = {}
        try:
            gingerBaseLock.acquire()
            package = get_dnf_package_info(pkg_name)
        except Exception, e:
            raise NotFoundError('GGBPKGUPD0003E', {'err': str(e)})
        finally:
            gingerBaseLock.release()
        return package

    def isRunning(self):
        """
        Return True whether the YUM package manager is already running or
        False otherwise.
        """
        pid = None
        try:
            for dnf_proc in process_iter():
                if 'dnf' in dnf_proc.name():
                    pid = dnf_proc.pid
                    break
        except:
            return False

        # the pidfile exists and it lives in process table
        return pid_exists(pid)


class AptUpdate(object):
    """
    Class to represent and operate with APT software update system.
    It's loaded only on those systems listed at APT_DISTROS and loads necessary
    modules in runtime.
    """
    def __init__(self):
        self.update_cmd = {'all': ['apt-get', 'upgrade', '-y'],
                           'specific': ['apt-get', '-y', '--only-upgrade',
                                        'install']}
        self.logfile = '/var/log/apt/term.log'
        self._apt_cache = getattr(__import__('apt'), 'Cache')()

    def getPackagesList(self):
        """
        Return a list of packages eligible to be updated by apt-get.
        """
        if self.isRunning():
            raise OperationFailed('GGBPKGUPD0005E')

        gingerBaseLock.acquire()
        try:
            self._apt_cache.update()
            self._apt_cache.upgrade()
            pkgs = self._apt_cache.get_changes()
        except Exception, e:
            raise OperationFailed('GGBPKGUPD0003E', {'err': e.message})
        finally:
            gingerBaseLock.release()

        return [pkg.shortname for pkg in pkgs]

    def getPackageInfo(self, pkg_name):
        """
        Get package information. The return is a dictionary containg the
        information about a package, in the format:

        package = {'package_name': <string>,
                   'version': <string>,
                   'arch': <string>,
                   'repository': <string>,
                   'depends': <list>
                  }
        """
        if self.isRunning():
            raise OperationFailed('GGBPKGUPD0005E')

        package = {}
        gingerBaseLock.acquire()
        try:
            self._apt_cache.upgrade()
            pkgs = self._apt_cache.get_changes()
        except Exception, e:
            raise OperationFailed('GGBPKGUPD0006E', {'err': e.message})
        finally:
            gingerBaseLock.release()

        pkg = next((x for x in pkgs if x.shortname == pkg_name), None)
        if not pkg:
            message = 'No package found'
            raise NotFoundError('GGBPKGUPD0006E', {'err': message})

        package = {'package_name': pkg.shortname,
                   'version': pkg.candidate.version,
                   'arch': pkg._pkg.architecture,
                   'repository': pkg.candidate.origins[0].label,
                   'depends': list(set([d[0].name for d in
                                       pkg.candidate.dependencies]))}
        return package

    def isRunning(self):
        """
        Return True whether the APT package manager is already running or
        False otherwise.
        """
        try:
            with open('/var/lib/dpkg/lock', 'w') as lockfile:
                fcntl.lockf(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)

        # cannot open dpkg lock file to write in exclusive mode means the
        # apt is currently running
        except IOError:
            return True

        return False


class ZypperUpdate(object):
    """
    Class to represent and operate with Zypper software update system.
    It's loaded only on those systems listed at ZYPPER_DISTROS and loads
    necessary modules in runtime.
    """
    def __init__(self):
        self.update_cmd = dict.fromkeys(['all', 'specific'],
                                        ["zypper", "--non-interactive",
                                         "update",
                                         "--auto-agree-with-licenses"])
        self.logfile = '/var/log/zypp/history'

    def getPackagesList(self):
        """
        Return a list of packages eligible to be updated by Zypper.
        """
        if self.isRunning():
            raise OperationFailed('GGBPKGUPD0005E')

        gingerBaseLock.acquire()
        packages = []
        cmd = ["zypper", "list-updates"]
        (stdout, stderr, returncode) = run_command(cmd)

        if len(stderr) > 0:
            raise OperationFailed('GGBPKGUPD0003E', {'err': stderr})

        for line in stdout.split('\n'):
            if line.startswith('v |'):
                packages.append(line.split(' | ')[2].strip())
        gingerBaseLock.release()
        return packages

    def getPackageInfo(self, pkg_name):
        """
        Get package information. The return is a dictionary containg the
        information about a package, in the format:

        package = {'package_name': <string>,
                   'version': <string>,
                   'arch': <string>,
                   'repository': <string>,
                   'depends': <list>
                  }
        """
        if self.isRunning():
            raise OperationFailed('GGBPKGUPD0005E')

        gingerBaseLock.acquire()
        cmd = ["zypper", "info", "--requires", pkg_name]
        (stdout, stderr, returncode) = run_command(cmd)

        if len(stderr) > 0:
            raise OperationFailed('GGBPKGUPD0006E', {'err': stderr})

        # Zypper returns returncode == 0 and stderr <= 0, even if package is
        # not found in it's base. Need check the output of the command to parse
        # correctly.
        stdout = stdout.split('\n')
        message = 'package \'%s\' not found.' % pkg_name
        if message in stdout:
            raise NotFoundError('GGBPKGUPD0006E', {'err': message})

        package = {}
        for (key, token) in (('repository', 'Repository:'),
                             ('version', 'Version:'),
                             ('arch', 'Arch:'),
                             ('package_name', 'Name:')):
            for line in stdout:
                if line.startswith(token):
                    package[key] = line.split(': ')[1].strip()
                    break

        # get the list of dependencies
        pkg_dep = []
        for line in stdout[stdout.index('Requires:')+1:len(stdout)-1]:
            # scan for valid lines with package names
            line = line.strip()
            if '.so' in line:
                continue
            if line.startswith('/'):
                continue
            if "python(abi)" in line:
                line = "python-base"
            pkg_dep.append(line.split()[0])
        pkg_dep = list(set(pkg_dep))
        package['depends'] = pkg_dep
        gingerBaseLock.release()
        return package

    def isRunning(self):
        """
        Return True whether the Zypper package manager is already running or
        False otherwise.
        """
        try:
            with open('/var/run/zypp.pid', 'r') as pidfile:
                pid = int(pidfile.read().rstrip('\n'))

        # cannot find pidfile, assumes yum is not running
        except (IOError, ValueError):
            return False

        # the pidfile exists and it lives in process table
        if pid_exists(pid):
            return True

        return False
