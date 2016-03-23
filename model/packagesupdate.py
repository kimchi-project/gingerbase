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

from wok.exception import OperationFailed
from wok.utils import add_task, wok_log
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
        try:
            self.host_swupdate = SoftwareUpdate()
        except:
            self.host_swupdate = None

    def lookup(self, name):
        if self.host_swupdate is None:
            raise OperationFailed('GGBPKGUPD0004E')

        return self.host_swupdate.getUpdate(name)


class SwUpdateProgressModel(object):
    def __init__(self, **kargs):
        self.task = TaskModel(**kargs)
        self.objstore = kargs['objstore']

    def lookup(self, *name):
        try:
            swupdate = SoftwareUpdate()
        except:
            raise OperationFailed('GGBPKGUPD0004E')

        taskid = add_task('/plugins/gingerbase/host/swupdateprogress',
                          swupdate.tailUpdateLogs, self.objstore, None)
        return self.task.lookup(taskid)
