# -*- coding: utf-8 -*-
#
# Project Ginger Base
#
# Copyright IBM Corp, 2013-2017
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

import json
import time
import unittest
from functools import partial

from tests.utils import patch_auth, request
from tests.utils import run_server, wait_task

from wok.rollbackcontext import RollbackContext

test_server = None


def setUpModule():
    global test_server

    patch_auth()
    test_server = run_server(test_mode=True)


def tearDownModule():
    test_server.stop()


class RestTests(unittest.TestCase):
    def _async_op(self, cb, opaque):
        time.sleep(1)
        cb('success', True)

    def _except_op(self, cb, opaque):
        time.sleep(1)
        raise Exception("Oops, this is an exception handle test."
                        " You can ignore it safely")
        cb('success', True)

    def _intermid_op(self, cb, opaque):
        time.sleep(1)
        cb('in progress')

    def setUp(self):
        self.request = partial(request)

    def _task_lookup(self, taskid):
        return json.loads(
            self.request('/tasks/%s' % taskid).read()
        )

    def assertHTTPStatus(self, code, *args):
        resp = self.request(*args)
        self.assertEquals(code, resp.status)

    def test_debugreports(self):
        resp = request('/plugins/gingerbase/debugreports')
        self.assertEquals(200, resp.status)

    def _report_delete(self, name):
        request('/plugins/gingerbase/debugreports/%s' % name, '{}', 'DELETE')

    def test_create_debugreport(self):
        req = json.dumps({'name': 'test_rest_report1'})
        with RollbackContext() as rollback:
            resp = request('/plugins/gingerbase/debugreports', req, 'POST')
            self.assertEquals(202, resp.status)
            task = json.loads(resp.read())
            # make sure the debugreport doesn't exist until the
            # the task is finished
            wait_task(self._task_lookup, task['id'])
            rollback.prependDefer(self._report_delete, 'test_rest_report2')
            resp = request(
                '/plugins/gingerbase/debugreports/test_rest_report1'
            )
            debugreport = json.loads(resp.read())
            self.assertEquals("test_rest_report1", debugreport['name'])
            self.assertEquals(200, resp.status)
            req = json.dumps({'name': 'test_rest_report2'})
            resp = request(
                '/plugins/gingerbase/debugreports/test_rest_report1',
                req, 'PUT'
            )
            self.assertEquals(303, resp.status)

    def test_debugreport_download(self):
        req = json.dumps({'name': 'test_rest_report1'})
        with RollbackContext() as rollback:
            resp = request('/plugins/gingerbase/debugreports', req, 'POST')
            self.assertEquals(202, resp.status)
            task = json.loads(resp.read())
            # make sure the debugreport doesn't exist until the
            # the task is finished
            wait_task(self._task_lookup, task['id'], 20)
            rollback.prependDefer(self._report_delete, 'test_rest_report1')
            resp = request(
                '/plugins/gingerbase/debugreports/test_rest_report1'
            )
            debugreport = json.loads(resp.read())
            self.assertEquals("test_rest_report1", debugreport['name'])
            self.assertEquals(200, resp.status)
            resp = request(
                '/plugins/gingerbase/debugreports/test_rest_report1/content'
            )
            self.assertEquals(200, resp.status)
            resp = request(
                '/plugins/gingerbase/debugreports/test_rest_report1'
            )
            debugre = json.loads(resp.read())
            resp = request('/' + debugre['uri'])
            self.assertEquals(200, resp.status)

    def test_repositories(self):
        def verify_repo(t, res):
            for field in ('repo_id', 'enabled', 'baseurl', 'config'):
                if field in t.keys():
                    self.assertEquals(t[field], res[field])

        base_uri = '/plugins/gingerbase/host/repositories'
        resp = self.request(base_uri)
        self.assertEquals(200, resp.status)
        # Already have one repo in Kimchi's system
        self.assertEquals(1, len(json.loads(resp.read())))

        # Create a repository
        repo = {'repo_id': 'fedora-fake',
                'baseurl': 'http://www.fedora.org'}
        req = json.dumps(repo)
        resp = self.request(base_uri, req, 'POST')
        self.assertEquals(201, resp.status)

        # Verify the repository
        res = json.loads(self.request('%s/fedora-fake' % base_uri).read())
        verify_repo(repo, res)

        # Update the repository
        params = {}
        params['baseurl'] = repo['baseurl'] = 'http://www.fedoraproject.org'
        resp = self.request('%s/fedora-fake' % base_uri, json.dumps(params),
                            'PUT')

        # Verify the repository
        res = json.loads(self.request('%s/fedora-fake' % base_uri).read())
        verify_repo(repo, res)

        # Delete the repository
        resp = self.request('%s/fedora-fake' % base_uri, '{}', 'DELETE')
        self.assertEquals(204, resp.status)
