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
from wok.exception import InvalidOperation
from wok.exception import InvalidParameter
from wok.exception import OperationFailed
from wok.plugins.gingerbase.model.smt import SmtModel


class SMTModelTests(unittest.TestCase):
    @mock.patch('wok.plugins.gingerbase.model.smt.SmtModel.check_smt_support')
    @mock.patch('wok.plugins.gingerbase.model.smt.SmtModel.'
                'get_persistent_settings_s390x')
    @mock.patch('wok.plugins.gingerbase.model.smt.SmtModel.'
                'get_current_settings_s390x')
    def test_get_smt_status_supported(self, mock_current,
                                      mock_persistent, mock_smt_suport):
        """
        Unittest to fetch smt status
        """
        current_info = {'status': 'enabled', 'smt': '2'}
        perisistent_info = {'status': 'enabled', 'smt': '2'}
        mock_smt_suport.return_value = True
        mock_current.return_value = current_info
        mock_persistent.return_value = perisistent_info
        smtmodel = SmtModel()
        out = smtmodel.get_smt_status_s390x()
        mock_smt_suport.assert_called_with()
        self.assertEqual(len(out), 2)

    @mock.patch('wok.plugins.gingerbase.model.smt.SmtModel.check_smt_support')
    def test_get_smt_status_notsupported(self, mock_smt_suport):
        """
        Unittest to fetch smt status when smt not supported.
        """
        mock_smt_suport.return_value = False
        with self.assertRaisesRegexp(OperationFailed, 'GINSMT0006E'):
            smtmodel = SmtModel()
            smtmodel.get_smt_status_s390x()
            mock_smt_suport.assert_called_with()

    @mock.patch('wok.plugins.gingerbase.model.smt.'
                'SmtModel.write_zipl_file')
    def test_write_to_conf(self, mock_write):
        """
        Unittest to write smt val to zipl file.
        """
        data = """
        [defaultboot]
default=linux
target=/boot
[linux]
        image=/boot/vmlinuz-4.4.0-25.44.el7_2.kvmibm1_1_3.1.s390x
        ramdisk=/boot/initramfs-4.4.0-25.44.el7_2.kvmibm1_1_3.1.s390x.img
        parameters="vconsole.keymap=us elevator=deadline pci=on zfcp.
        allow_lun_scan=0 root=/dev/mapper/zkvm-root rd.lvm.lv=zkvm/root
        crashkernel=128M rd.zfcp=0.0.9200,0x50050763071046a6,
        0x4013400f00000000 LANG=en_US.UTF-8 rd.zfcp=0.0.9200,
        0x50050763070386a6,0x4013400f00000000 vconsole.font=latarcyrhe smt=2"
       """
        name = 'dummy'
        smt_val = 2
        open_mock = mock.mock_open(read_data=data)
        with mock.patch('wok.plugins.ginger.model.utils.open',
                        open_mock, create=True):
            smtmodel = SmtModel()
            smtmodel.write_zipl_file(name, smt_val)
            mock_write.return_value = {}
            smtmodel.write_zipl_file(name, smt_val)

    @mock.patch('wok.plugins.gingerbase.model.smt.shutil')
    @mock.patch('os.path.isfile')
    @mock.patch('wok.plugins.gingerbase.model.smt.SmtModel.write_zipl_file')
    @mock.patch('wok.plugins.gingerbase.model.smt.SmtModel.load_smt_s390x')
    def test_enable_s390x_success(self, mock_load, mock_write,
                                  mock_is_file, mock_shutil):
        """
        Unittest to enable SMT success scenario.
        """
        smt_val = '1'
        name = 'dummy'
        mock_is_file.return_value = True
        mock_shutil.return_value = {}
        mock_write.return_value = {}
        mock_load.return_value = {}
        smtmodel = SmtModel()
        smtmodel.enable_smt_s390x(name, smt_val)

    @mock.patch('wok.plugins.gingerbase.model.smt.SmtModel.write_zipl_file')
    @mock.patch('wok.plugins.gingerbase.model.smt.SmtModel.load_smt_s390x')
    def test_enable_s390x_invalid(self, mock_load, mock_write):
        """
        Unittest to enable SMT for invalid parameter.
        """
        name = 'dummy'
        smt_val = 'sdsd'
        mock_write.return_value = {}
        mock_load.return_value = {}
        smtmodel = SmtModel()
        self.assertRaises(InvalidParameter, smtmodel.enable_smt_s390x,
                          smt_val, name)

    @mock.patch('wok.plugins.gingerbase.model.smt.fileinput')
    @mock.patch('wok.plugins.gingerbase.model.smt.shutil')
    @mock.patch('os.path.isfile')
    @mock.patch('wok.plugins.gingerbase.model.smt.SmtModel.'
                'get_smt_status_s390x')
    @mock.patch('wok.plugins.gingerbase.model.smt.SmtModel.load_smt_s390x')
    def test_disable_success(self, mock_load, mock_get, mock_is_file,
                             mock_shutil, mock_fileinput):
        """
        Unittest for disabling SMT success scenario.
        """
        info = {
            'persisted_smt_settings': {'status': 'enabled', 'smt': '2'},
            'current_smt_settings': {'status': 'enabled', 'smt': 'nosmt'}
        }
        name = 'dummy'
        mock_get.return_value = info
        mock_is_file.return_value = True
        mock_shutil.return_value = {}
        mock_fileinput.return_value = {}
        mock_load.return_value = {}
        smtmodel = SmtModel()
        smtmodel.disable_smt_s390x(name)

    @mock.patch('os.path.isfile')
    @mock.patch('wok.plugins.gingerbase.model.smt.SmtModel.'
                'get_smt_status_s390x')
    @mock.patch('wok.plugins.gingerbase.model.smt.SmtModel.load_smt_s390x')
    def test_disable_s390x_invalid(self, mock_load, mock_get, mock_is_file):
        """
        Unittest to disable SMT invalid scenario.
        """
        info = {
            'persisted_smt_settings': {'status': 'enabled', 'smt': '2'},
            'current_smt_settings': {'status': 'disabled', 'smt': 'nosmt'}
        }
        name = 'dummy'

        with self.assertRaisesRegexp(InvalidOperation, 'GINSMT0005E'):
            mock_get.return_value = info
            mock_is_file.return_value = True
            mock_load.return_value = {}
            smtmodel = SmtModel()
            smtmodel.disable_smt_s390x(name)

    @mock.patch('wok.plugins.gingerbase.model.smt.run_command')
    def test_load_smt_s390x(self, mock_run):
        """
        Unittest to load SMT.
        """
        backup = 'dfdf'
        mock_run.return_value = ['', '', 0]
        command = ['zipl']
        smtmodel = SmtModel()
        smtmodel.load_smt_s390x(backup)
        mock_run.assert_called_once_with(command)

    @mock.patch('wok.plugins.gingerbase.model.smt.LsCpu.get_threads_per_core')
    @mock.patch('wok.plugins.gingerbase.model.smt.run_command')
    def test_get_current_smt_s390x(self, mock_run, mock_threads):
        """
        Unittest to get the current SMT setting from /proc/cmdline
        """
        output = 'elevator=deadline crashkernel=196M ' \
                 'zfcp.no_auto_port_rescan=1 zfcp.' \
                 'allow_lun_scan=0 cmma=on pci=on ' \
                 'root=/dev/disk/by-path/ccw-0.0.518e-part1 ' \
                 'rd_DASD=0.0.518e BOOT_IMAGE=0 smt=1'
        mock_threads.return_value = 1
        mock_run.return_value = [output, '', 0]
        smtmodel = SmtModel()
        out = smtmodel.get_current_settings_s390x()
        self.assertEqual(out['smt'], 1)
        self.assertEqual(out['status'], 'enabled')
