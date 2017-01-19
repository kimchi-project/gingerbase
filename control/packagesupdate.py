#
# Project Ginger Base
#
# Copyright IBM Corp, 2016-2017
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

from wok import template
from wok.control.base import AsyncResource, Collection, Resource
from wok.control.base import SimpleCollection
from wok.control.utils import get_class_name, model_fn


PACKAGEUPDATE_ACTIVITY = {'POST': {'upgrade': "GGBPKGUPD0002L"}}


class PackagesUpdate(Collection):
    def __init__(self, model):
        super(PackagesUpdate, self).__init__(model)
        self.admin_methods = ['GET']
        self.resource = PackageUpdate

    def get(self, filter_params):
        res_list = []
        get_list = getattr(self.model, model_fn(self, 'get_list'))
        res_list = get_list(*self.model_args, **filter_params)
        return template.render(get_class_name(self), res_list)


class PackageUpdate(Resource):
    def __init__(self, model, id=None):
        super(PackageUpdate, self).__init__(model, id)
        self.admin_methods = ['GET', 'POST']
        self.upgrade = self.generate_action_handler_task('upgrade')
        self.log_map = PACKAGEUPDATE_ACTIVITY
        self.deps = PackageDeps(self.model, id)

    @property
    def data(self):
        return self.info


class PackageDeps(SimpleCollection):
    def __init__(self, model, pkg=None):
        super(PackageDeps, self).__init__(model)
        self.admin_methods = ['GET']
        self.pkg = pkg
        self.resource_args = [self.pkg, ]
        self.model_args = [self.pkg, ]


class SwUpdateProgress(AsyncResource):
    def __init__(self, model, id=None):
        super(SwUpdateProgress, self).__init__(model, id)
        self.admin_methods = ['GET']

    @property
    def data(self):
        return self.info
