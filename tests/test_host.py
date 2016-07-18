# -*- coding: utf-8 -*-
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

import json
import mock
import os
import platform
import psutil
import tempfile
import time
import unittest

from functools import partial
from mock import patch

from tests.utils import get_free_port, patch_auth, request
from tests.utils import run_server, wait_task

from wok.plugins.gingerbase.mockmodel import MockModel
from wok.plugins.gingerbase.model.host import HostModel


test_server = None
model = None
host = None
ssl_port = None
tmpfile = None


def setUpModule():
    global test_server, model, host, ssl_port, tmpfile

    patch_auth()
    tmpfile = tempfile.mktemp()
    model = MockModel(tmpfile)
    host = '127.0.0.1'
    port = get_free_port('http')
    ssl_port = get_free_port('https')
    cherrypy_port = get_free_port('cherrypy_port')
    test_server = run_server(host, port, ssl_port, test_mode=True,
                             cherrypy_port=cherrypy_port, model=model)


def tearDownModule():
    test_server.stop()
    os.unlink(tmpfile)


class HostTests(unittest.TestCase):
    def setUp(self):
        self.request = partial(request, host, ssl_port)

    def test_hostinfo(self):
        resp = self.request('/plugins/gingerbase/host').read()
        info = json.loads(resp)
        if platform.machine().startswith('s390x'):
            keys = ['os_distro', 'os_version', 'os_codename', 'cpu_model',
                    'memory', 'cpus', 'architecture', 'host', 'virtualization',
                    'cpu_threads']
        else:
            keys = ['os_distro', 'os_version', 'os_codename', 'cpu_model',
                    'memory', 'cpus', 'architecture', 'host',
                    'cpu_threads']
            try:
                total_phymem = psutil.TOTAL_PHYMEM
            except AttributeError:
                total_phymem = psutil.virtual_memory().total
            self.assertEquals(total_phymem, info['memory']['online'])
        self.assertEquals(sorted(keys), sorted(info.keys()))

        distro, version, codename = platform.linux_distribution()
        self.assertEquals(distro, info['os_distro'])
        self.assertEquals(version, info['os_version'])
        self.assertEquals(unicode(codename, "utf-8"), info['os_codename'])
        self.assertEqual(platform.node(), info['host'])
        self.assertEqual(platform.machine(), info['architecture'])

    def test_hoststats(self):
        time.sleep(1)
        stats_keys = ['cpu_utilization', 'memory', 'disk_read_rate',
                      'disk_write_rate', 'net_recv_rate', 'net_sent_rate']
        resp = self.request('/plugins/gingerbase/host/stats').read()
        stats = json.loads(resp)
        self.assertEquals(sorted(stats_keys), sorted(stats.keys()))

        cpu_utilization = stats['cpu_utilization']
        self.assertIsInstance(cpu_utilization, float)
        self.assertGreaterEqual(cpu_utilization, 0.0)
        self.assertTrue(cpu_utilization <= 100.0)

        memory_stats = stats['memory']
        self.assertIn('total', memory_stats)
        self.assertIn('free', memory_stats)
        self.assertIn('cached', memory_stats)
        self.assertIn('buffers', memory_stats)
        self.assertIn('avail', memory_stats)

        resp = self.request('/plugins/gingerbase/host/stats/history').read()
        history = json.loads(resp)
        self.assertEquals(sorted(stats_keys), sorted(history.keys()))

    def test_host_actions(self):
        resp = self.request('/plugins/gingerbase/host/shutdown', '{}', 'POST')
        self.assertEquals(200, resp.status)
        resp = self.request('/plugins/gingerbase/host/reboot', '{}', 'POST')
        self.assertEquals(200, resp.status)

    def test_packages_update(self):
        def _task_lookup(taskid):
            return json.loads(self.request('/plugins/gingerbase/tasks/%s' %
                                           taskid).read())

        resp = self.request('/plugins/gingerbase/host/packagesupdate',
                            None, 'GET')
        pkgs = json.loads(resp.read())
        self.assertEquals(5, len(pkgs))

        pkg_keys = ['package_name', 'repository', 'arch', 'version', 'depends']
        for p in pkgs:
            name = p['package_name']
            resp = self.request('/plugins/gingerbase/host/packagesupdate/' +
                                name, None, 'GET')
            info = json.loads(resp.read())
            self.assertEquals(sorted(pkg_keys), sorted(info.keys()))

        # Test system update of specific package. Since package 'ginger' has
        # 'wok' as dependency, both packages must be selected to be updated
        # and, in the end of the process, we have only 3 packages to update.
        uri = '/plugins/gingerbase/host/packagesupdate/ginger/upgrade'
        resp = self.request(uri, '{}', 'POST')
        task = json.loads(resp.read())
        task_params = [u'id', u'message', u'status', u'target_uri']
        self.assertEquals(sorted(task_params), sorted(task.keys()))

        resp = self.request('/plugins/gingerbase/tasks/' + task[u'id'],
                            None, 'GET')
        task_info = json.loads(resp.read())
        self.assertEquals(task_info['status'], 'running')
        wait_task(_task_lookup, task_info['id'])
        resp = self.request('/plugins/gingerbase/tasks/' + task[u'id'],
                            None, 'GET')
        task_info = json.loads(resp.read())
        self.assertEquals(task_info['status'], 'finished')
        self.assertIn(u'All packages updated', task_info['message'])
        pkgs = model.packagesupdate_get_list()
        self.assertEquals(3, len(pkgs))

        # test system update of the rest of packages
        resp = self.request('/plugins/gingerbase/host/swupdate', '{}', 'POST')
        task = json.loads(resp.read())
        task_params = [u'id', u'message', u'status', u'target_uri']
        self.assertEquals(sorted(task_params), sorted(task.keys()))

        resp = self.request('/tasks/' + task[u'id'], None, 'GET')
        task_info = json.loads(resp.read())
        self.assertEquals(task_info['status'], 'running')
        wait_task(_task_lookup, task_info['id'])
        resp = self.request('/tasks/' + task[u'id'], None, 'GET')
        task_info = json.loads(resp.read())
        self.assertEquals(task_info['status'], 'finished')
        self.assertIn(u'All packages updated', task_info['message'])
        pkgs = model.packagesupdate_get_list()
        self.assertEquals(0, len(pkgs))

    def test_swupdateprogress(self):
        resp = self.request('/plugins/gingerbase/host/swupdateprogress',
                            None, 'GET')
        task = json.loads(resp.read())
        self.assertEquals(202, resp.status)

        for i in xrange(1, 6):
            resp = self.request('/tasks/' + task['id'], None, 'GET')
            task = json.loads(resp.read())
            self.assertEquals(200, resp.status)
            self.assertIn('*', task['message'].rstrip('\n'))
            time.sleep(1)

        resp = self.request('/tasks/' + task['id'], None, 'GET')
        task = json.loads(resp.read())
        self.assertEquals(200, resp.status)
        self.assertEqual(task['status'], 'finished')
        time.sleep(1)

    def test_get_vmlist_bystate_import_error(self):
        with patch.dict('sys.modules', {}):
            vms = HostModel(objstore=None).get_vmlist_bystate()
            self.assertEqual(vms, [])

    @mock.patch('wok.plugins.gingerbase.model.host.run_command')
    def test_vmlist_bystate_libvirtd_not_running(self, mock_run_cmd):
        mock_run_cmd.return_value = ['', '', 3]
        with patch.dict('sys.modules', {'libvirt': 0}):
            vms = HostModel(objstore=None).get_vmlist_bystate()
            self.assertEqual(vms, [])
            cmd = ['systemctl', 'is-active', 'libvirtd', '--quiet']
            mock_run_cmd.assert_called_once_with(cmd, silent=True)
