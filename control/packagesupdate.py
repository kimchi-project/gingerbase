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

from wok.control.base import AsyncResource, Collection, Resource


class PackagesUpdate(Collection):
    def __init__(self, model):
        super(PackagesUpdate, self).__init__(model)
        self.role_key = 'updates'
        self.admin_methods = ['GET']
        self.resource = PackageUpdate


class PackageUpdate(Resource):
    def __init__(self, model, id=None):
        super(PackageUpdate, self).__init__(model, id)
        self.role_key = 'updates'
        self.admin_methods = ['GET']

    @property
    def data(self):
        return self.info


class SwUpdateProgress(AsyncResource):
    def __init__(self, model, id=None):
        super(SwUpdateProgress, self).__init__(model, id)
        self.role_key = 'updates'
        self.admin_methods = ['GET']

    @property
    def data(self):
        return self.info
