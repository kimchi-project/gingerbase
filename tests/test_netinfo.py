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

import mock
import unittest

from mock import call

import wok.plugins.gingerbase.netinfo as netinfo


class NetinfoTests(unittest.TestCase):

    @mock.patch('wok.plugins.gingerbase.netinfo.all_interfaces')
    @mock.patch('wok.plugins.gingerbase.netinfo.get_interface_kernel_module')
    def test_get_interfaces_loaded_with_modules(self, mock_kernel_mod,
                                                mock_all_ifaces):

        mock_all_ifaces.return_value = ['iface1', 'iface2', 'iface3']
        mock_kernel_mod.side_effect = ['mod1', 'unknown', 'mod1']

        module = 'mod1'

        self.assertEqual(
            netinfo.get_interfaces_loaded_with_modules([module]),
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
            netinfo.get_interfaces_loaded_with_modules(modules),
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
            netinfo.get_interfaces_loaded_with_modules(modules), []
        )
        mock_all_ifaces.assert_called_once_with()
        mock_kernel_mod.assert_has_calls(
            [call('iface1'), call('iface2'), call('iface3'), call('iface4')]
        )
