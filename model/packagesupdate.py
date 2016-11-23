#
# Project Ginger Base
#
# Copyright IBM Corp, 2016
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

from wok.asynctask import AsyncTask
from wok.exception import OperationFailed
from wok.utils import wok_log
from wok.model.tasks import TaskModel

from wok.plugins.gingerbase.swupdate import SoftwareUpdate


class PackagesUpdateModel(object):
    def __init__(self, **kargs):
        try:
            self.host_swupdate = SoftwareUpdate()
        except:
            self.host_swupdate = None

    def get_list(self):
        if self.host_swupdate is None:
            raise OperationFailed('GGBPKGUPD0004E')

        return self.host_swupdate.getUpdates()


class PackageUpdateModel(object):
    def __init__(self, **kargs):
        self.task = TaskModel(**kargs)
        self.objstore = kargs['objstore']
        self.pkgs2update = []
        try:
            self.host_swupdate = SoftwareUpdate()
        except:
            self.host_swupdate = None

    def lookup(self, name):
        if self.host_swupdate is None:
            raise OperationFailed('GGBPKGUPD0004E')

        return self.host_swupdate.getUpdate(name)

    def _resolve_dependencies(self, package=None, dep_list=None):
        """
        Resolve the dependencies for a given package from the dictionary of
        eligible packages to be upgraded.
        """
        if dep_list is None:
            dep_list = []
        if package is None:
            return []
        dep_list.append(package)
        deps = self.host_swupdate.getUpdate(package)['depends']
        for pkg in set(deps).intersection(self.pkgs2update):
            if pkg in dep_list:
                break
            self._resolve_dependencies(pkg, dep_list)
        return dep_list

    def upgrade(self, name):
        """
        Execute the update of a specific package (and its dependencies, if
        necessary) in the system.

        @param: Name
        @return: task
        """
        if self.host_swupdate is None:
            raise OperationFailed('GGBPKGUPD0004E')

        self.pkgs2update = self.host_swupdate.getUpdates()
        pkgs_list = self._resolve_dependencies(name)
        msg = 'The following packages will be updated: ' + ', '.join(pkgs_list)
        wok_log.debug(msg)
        taskid = AsyncTask('/plugins/gingerbase/host/packagesupdate/%s/upgrade'
                           % name, self.host_swupdate.doUpdate, pkgs_list).id
        return self.task.lookup(taskid)


class PackageDepsModel(object):
    def __init__(self, **kargs):
        try:
            self.host_swupdate = SoftwareUpdate()
        except:
            self.host_swupdate = None

    def get_list(self, pkg):
        return self.host_swupdate.getPackageDeps(pkg)


class SwUpdateProgressModel(object):
    def __init__(self, **kargs):
        self.task = TaskModel(**kargs)
        self.objstore = kargs['objstore']

    def lookup(self, *name):
        try:
            swupdate = SoftwareUpdate()
        except:
            raise OperationFailed('GGBPKGUPD0004E')

        taskid = AsyncTask('/plugins/gingerbase/host/swupdateprogress',
                           swupdate.tailUpdateLogs).id
        return self.task.lookup(taskid)
