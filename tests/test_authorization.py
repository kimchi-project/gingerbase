#
# Project Ginger Base
#
# Copyright IBM Corp, 2014-2016
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

import os
import unittest
from functools import partial

from tests.utils import patch_auth, request, run_server

from wok.plugins.gingerbase import mockmodel


test_server = None
model = None
fake_iso = '/tmp/fake.iso'


def setUpModule():
    global test_server, model

    patch_auth(sudo=False)
    model = mockmodel.MockModel('/tmp/obj-store-test')
    test_server = run_server(test_mode=True, model=model)


def tearDownModule():
    test_server.stop()
    os.unlink('/tmp/obj-store-test')


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.request = partial(request)
        model.reset()

    def test_nonroot_access(self):
        # Non-root users can access static host information
        resp = self.request('/plugins/gingerbase/host', '{}', 'GET')
        self.assertEquals(200, resp.status)

        # Non-root users can access host stats
        resp = self.request('/plugins/gingerbase/host/stats', '{}', 'GET')
        self.assertEquals(200, resp.status)

        # Non-root users can not reboot/shutdown host system
        resp = self.request('/plugins/gingerbase/host/reboot', '{}', 'POST')
        self.assertEquals(403, resp.status)
        resp = self.request('/plugins/gingerbase/host/shutdown', '{}', 'POST')
        self.assertEquals(403, resp.status)

        # Normal users can not upgrade packages
        uri = '/plugins/gingerbase/host/packagesupdate/ginger/upgrade'
        resp = self.request(uri, '{}', 'POST')
        self.assertEquals(403, resp.status)
        resp = self.request('/plugins/gingerbase/host/swupdate', '{}', 'POST')
        self.assertEquals(403, resp.status)
