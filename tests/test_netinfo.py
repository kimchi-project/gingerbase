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
import unittest

import mock
import wok.plugins.gingerbase.netinfo as netinfo
from mock import call


class NetinfoTests(unittest.TestCase):

    @mock.patch('wok.plugins.gingerbase.netinfo.all_interfaces')
    @mock.patch('wok.plugins.gingerbase.netinfo.get_interface_kernel_module')
    def test_get_interfaces_loaded_with_modules(self, mock_kernel_mod,
                                                mock_all_ifaces):

        mock_all_ifaces.return_value = ['iface1', 'iface2', 'iface3']
        mock_kernel_mod.side_effect = ['mod1', 'unknown', 'mod1']

        module = 'mod1'

        self.assertEqual(
            netinfo.get_interfaces_with_modules([module]),
            ['iface1', 'iface3']
        )
        mock_all_ifaces.assert_called_once_with()
        mock_kernel_mod.assert_has_calls(
            [call('iface1'), call('iface2'), call('iface3')]
        )

    @mock.patch('wok.plugins.gingerbase.netinfo.all_interfaces')
    @mock.patch('wok.plugins.gingerbase.netinfo.get_interface_kernel_module')
    def test_get_interfaces_loaded_multiple_modules(self, mock_kernel_mod,
                                                    mock_all_ifaces):

        modules = ['mlx4_core', 'mlx5_core']

        mock_all_ifaces.return_value = [
            'iface1', 'iface2', 'iface3', 'iface4'
        ]
        mock_kernel_mod.side_effect = [
            'mod1', 'mlx4_core', 'unknown', 'mlx5_core'
        ]

        self.assertEqual(
            netinfo.get_interfaces_with_modules(modules),
            ['iface2', 'iface4']
        )
        mock_all_ifaces.assert_called_once_with()
        mock_kernel_mod.assert_has_calls(
            [call('iface1'), call('iface2'), call('iface3'), call('iface4')]
        )

    @mock.patch('wok.plugins.gingerbase.netinfo.all_interfaces')
    @mock.patch('wok.plugins.gingerbase.netinfo.get_interface_kernel_module')
    def test_get_interfaces_loaded_not_found(self, mock_kernel_mod,
                                             mock_all_ifaces):

        modules = ['not_valid_mod1', 'not_valid_mod2']

        mock_all_ifaces.return_value = [
            'iface1', 'iface2', 'iface3', 'iface4'
        ]
        mock_kernel_mod.side_effect = [
            'mod1', 'mlx4_core', 'unknown', 'mlx5_core'
        ]

        self.assertEqual(
            netinfo.get_interfaces_with_modules(modules), []
        )
        mock_all_ifaces.assert_called_once_with()
        mock_kernel_mod.assert_has_calls(
            [call('iface1'), call('iface2'), call('iface3'), call('iface4')]
        )

    @mock.patch('wok.plugins.gingerbase.netinfo.get_interface_kernel_module')
    def test_is_interface_rdma_capable_true(self, mock_kernel_mod):
        mock_kernel_mod.return_value = 'mlx5_core'
        self.assertTrue(netinfo.is_interface_rdma_capable('iface1'))
        mock_kernel_mod.assert_called_once_with('iface1')

    @mock.patch('wok.plugins.gingerbase.netinfo.get_interface_kernel_module')
    def test_is_interface_rdma_capable_false(self, mock_kernel_mod):
        mock_kernel_mod.return_value = 'not_mlx5_core'
        self.assertFalse(netinfo.is_interface_rdma_capable('iface1'))
        mock_kernel_mod.assert_called_once_with('iface1')

    @mock.patch('wok.plugins.gingerbase.netinfo.run_command')
    def test_is_rdma_service_enabled_first_service(self, mock_run_cmd):
        mock_run_cmd.return_value = ['', '', 0]
        self.assertTrue(netinfo.is_rdma_service_enabled())
        mock_run_cmd.assert_called_once_with(
            ['systemctl', 'is-active', 'rdma', '--quiet'], silent=True
        )

    @mock.patch('wok.plugins.gingerbase.netinfo.run_command')
    def test_is_rdma_service_enabled_second_service(self, mock_run_cmd):
        mock_run_cmd.side_effect = [['', '', 3], ['', '', 0]]
        self.assertTrue(netinfo.is_rdma_service_enabled())
        mock_run_cmd.assert_has_calls(
            [
                call(['systemctl', 'is-active', 'rdma', '--quiet'],
                     silent=True),
                call(['systemctl', 'is-active', 'openibd', '--quiet'],
                     silent=True)
            ]
        )

    @mock.patch('wok.plugins.gingerbase.netinfo.run_command')
    def test_is_rdma_service_enabled_false(self, mock_run_cmd):
        mock_run_cmd.side_effect = [['', '', 3], ['', '', 3]]
        self.assertFalse(netinfo.is_rdma_service_enabled())
        mock_run_cmd.assert_has_calls(
            [
                call(['systemctl', 'is-active', 'rdma', '--quiet'],
                     silent=True),
                call(['systemctl', 'is-active', 'openibd', '--quiet'],
                     silent=True)
            ]
        )

    @mock.patch('wok.plugins.gingerbase.netinfo.is_rdma_service_enabled')
    @mock.patch('wok.plugins.gingerbase.netinfo.is_interface_rdma_capable')
    def test_is_rdma_enabled_true(self, mock_iface_rdma,
                                  mock_service_enabled):

        mock_iface_rdma.return_value = True
        mock_service_enabled.return_value = True

        self.assertTrue(netinfo.is_rdma_enabled('iface1'))
        mock_iface_rdma.assert_called_once_with('iface1')
        mock_service_enabled.assert_called_once_with()

    @mock.patch('wok.plugins.gingerbase.netinfo.is_rdma_service_enabled')
    @mock.patch('wok.plugins.gingerbase.netinfo.is_interface_rdma_capable')
    def test_is_rdma_enabled_wrong_mod(self, mock_iface_rdma,
                                       mock_service_enabled):

        mock_iface_rdma.return_value = False
        mock_service_enabled.return_value = True

        self.assertFalse(netinfo.is_rdma_enabled('iface1'))
        mock_iface_rdma.assert_called_once_with('iface1')
        mock_service_enabled.assert_not_called()

    @mock.patch('wok.plugins.gingerbase.netinfo.is_rdma_service_enabled')
    @mock.patch('wok.plugins.gingerbase.netinfo.is_interface_rdma_capable')
    def test_is_rdma_enabled_no_service(self, mock_iface_rdma,
                                        mock_service_enabled):

        mock_iface_rdma.return_value = True
        mock_service_enabled.return_value = False

        self.assertFalse(netinfo.is_rdma_enabled('iface1'))
        mock_iface_rdma.assert_called_once_with('iface1')
        mock_service_enabled.assert_called_once_with()

    @mock.patch('wok.plugins.gingerbase.netinfo.all_interfaces')
    @mock.patch('wok.plugins.gingerbase.netinfo.is_rdma_service_enabled')
    @mock.patch('wok.plugins.gingerbase.netinfo.is_interface_rdma_capable')
    def test_get_rdma_enabled_ifaces(self, mock_iface_rdma,
                                     mock_service_enabled, mock_all_ifaces):
        mock_all_ifaces.return_value = [
            'iface1', 'iface2', 'iface3', 'iface4'
        ]
        mock_iface_rdma.side_effect = [True, False, False, True]
        mock_service_enabled.return_value = True

        self.assertEqual(netinfo.get_rdma_enabled_interfaces(),
                         ['iface1', 'iface4'])

        mock_service_enabled.assert_called_once_with()
        mock_all_ifaces.assert_called_once_with()

        mock_iface_rdma.assert_has_calls(
            [call('iface1'), call('iface2'), call('iface3'), call('iface4')]
        )

    @mock.patch('wok.plugins.gingerbase.netinfo.all_interfaces')
    @mock.patch('wok.plugins.gingerbase.netinfo.is_rdma_service_enabled')
    @mock.patch('wok.plugins.gingerbase.netinfo.is_interface_rdma_capable')
    def test_get_rdma_enabled_ifaces_no_service(self, mock_iface_rdma,
                                                mock_service_enabled,
                                                mock_all_ifaces):
        mock_service_enabled.return_value = False

        self.assertEqual(netinfo.get_rdma_enabled_interfaces(), [])

        mock_service_enabled.assert_called_once_with()
        mock_iface_rdma.assert_not_called()
        mock_all_ifaces.assert_not_called()

    @mock.patch('os.readlink')
    def test_get_mlx5_nic_bus_id(self, mock_readlink):
        mock_readlink.return_value = '.../../../../0001:01.1'

        bus_id = netinfo.get_mlx5_nic_bus_id('iface1')
        mock_readlink.assert_called_once_with(
            '/sys/class/net/%s/device' % 'iface1'
        )
        self.assertEqual(bus_id, '0001:01.1')

    @mock.patch('wok.plugins.gingerbase.netinfo.run_command')
    @mock.patch('wok.plugins.gingerbase.netinfo.get_mlx5_nic_bus_id')
    def test_get_mlx5_nic_type_virtual(self, mock_bus_id, mock_run_cmd):
        mock_bus_id.return_value = '0001:01.1'
        lspci_output = 'Ethernet controller: Mellanox Technologies ' \
            'MT27700 Family [ConnectX-4 Virtual Function]'
        mock_run_cmd.return_value = [lspci_output, '', 0]

        nic_type = netinfo.get_mlx5_nic_type('iface1')

        mock_bus_id.assert_called_once_with('iface1')
        mock_run_cmd.assert_called_once_with(
            ['lspci', '-s', '0001:01.1']
        )
        self.assertEqual(nic_type, 'virtual')

    @mock.patch('wok.plugins.gingerbase.netinfo.run_command')
    @mock.patch('wok.plugins.gingerbase.netinfo.get_mlx5_nic_bus_id')
    def test_get_mlx5_nic_type_physical(self, mock_bus_id, mock_run_cmd):
        mock_bus_id.return_value = '0001:01.1'
        lspci_output = 'Ethernet controller: Mellanox Technologies ' \
            'MT27700 Family [ConnectX-4]'
        mock_run_cmd.return_value = [lspci_output, '', 0]

        nic_type = netinfo.get_mlx5_nic_type('iface1')

        mock_bus_id.assert_called_once_with('iface1')
        mock_run_cmd.assert_called_once_with(
            ['lspci', '-s', '0001:01.1']
        )
        self.assertEqual(nic_type, 'physical')

    @mock.patch('wok.plugins.gingerbase.netinfo.get_interface_kernel_module')
    @mock.patch('wok.plugins.gingerbase.netinfo.get_mlx5_nic_type')
    def test_get_nic_type_non_mlx5(self, mock_mlx5_nic_type,
                                   mock_kernel_mod):
        mock_kernel_mod.return_value = 'any_driver'

        nic_type = netinfo.get_nic_type('iface1')

        mock_kernel_mod.assert_called_once_with('iface1')
        mock_mlx5_nic_type.assert_not_called()
        self.assertEqual(nic_type, 'physical')

    @mock.patch('wok.plugins.gingerbase.netinfo.get_interface_kernel_module')
    @mock.patch('wok.plugins.gingerbase.netinfo.get_mlx5_nic_type')
    def test_get_nic_type_mlx5_virtual(self, mock_mlx5_nic_type,
                                       mock_kernel_mod):
        mock_kernel_mod.return_value = 'mlx5_core'
        mock_mlx5_nic_type.return_value = 'virtual'

        nic_type = netinfo.get_nic_type('iface1')

        mock_kernel_mod.assert_called_once_with('iface1')
        mock_mlx5_nic_type.assert_called_once_with('iface1')
        self.assertEqual(nic_type, 'virtual')
