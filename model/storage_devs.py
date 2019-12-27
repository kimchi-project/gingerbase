#
# Project Ginger Base
#
# Copyright IBM Corp, 2016
#
# Code derived from Project Ginger
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
import binascii
import glob
import os
import platform
import re

from wok.exception import OperationFailed
from wok.utils import run_command

FC_PATHS = '/dev/disk/by-path/*fc*'
PATTERN_CCW = 'ccw-(?P<hba_id>[\\d.]+)-zfcp-(?P<wwpn>[\\w]+):(?P<fcp_lun>[\\w]+)$'
PATTERN_PCI = 'pci-(?P<hba_id>[\\d.:]+)(-vport-(?P<vport>[\\w]+))?-fc-' \
              '(?P<wwpn>[\\w]+)-lun-(?P<fcp_lun>[\\d]+)$'


class StorageDevsModel(object):
    """
    Model to represent the list of storage devices
    """

    def get_list(self):

        return get_final_list()


def get_final_list():
    """
    Comprehensive list of storage devices found on the system
    :return:List of dictionaries containing the information about
            individual disk
    """
    try:
        out = get_lsblk_keypair_out(True)
    except OperationFailed:
        out = get_lsblk_keypair_out(False)

    final_list = []

    try:
        dasds = get_dasd_devs()
        if dasds:
            final_list = dasds

        blk_dict = parse_lsblk_out(out)

        out = get_disks_by_id_out()
        ll_dict, ll_id_dict = parse_ll_out(out)

        fc_blk_dict = get_fc_path_elements()

        for blk in blk_dict:
            final_dict = {}
            if blk in ll_dict:
                final_dict['id'] = ll_dict[blk]
                if final_dict['id'].startswith('ccw-'):
                    continue

                block_dev_list = ll_id_dict[final_dict['id']]
                max_slaves = 1
                for block_dev in block_dev_list:
                    slaves = os.listdir('/sys/block/' + block_dev + '/slaves/')
                    if max_slaves < len(slaves):
                        max_slaves = len(slaves)

                final_dict['mpath_count'] = max_slaves

            final_dict['name'] = blk
            final_dict['size'] = blk_dict[blk]['size']
            final_dict['type'] = blk_dict[blk]['transport']

            if final_dict['type'] == 'fc':
                final_dict['hba_id'] = fc_blk_dict[blk].get('hba_id', '')
                final_dict['wwpn'] = fc_blk_dict[blk].get('wwpn', '')
                final_dict['fcp_lun'] = fc_blk_dict[blk].get('fcp_lun', '')
                final_dict['vport'] = fc_blk_dict[blk].get('vport', '')

            if 'id' in final_dict:
                if final_dict['id'] in ll_id_dict:
                    final_dict['name'] = ll_id_dict[final_dict['id']][0]
                if 'hba_id' in final_dict.keys():
                    if final_dict['hba_id']:
                        final_list.append(final_dict)
                else:
                    final_list.append(final_dict)
    except Exception as e:
        raise OperationFailed('GINSD00005E', {'err': e.message})

    return final_list


def get_dasd_devs():
    """
    Get the list of unformatted DASD devices
    """
    devs = []
    if platform.machine() == 's390x':
        dasd_pim_dict = _get_dasd_pim()
        dasd_devices = _get_lsdasd_devs()
        for device in dasd_devices:
            uf_dev = {}
            uf_dev['type'] = 'dasd'
            uf_dev['name'] = device['name']
            uf_dev['mpath_count'] = 'N/A'
            dasdsize = device['size']
            if dasdsize == 'Unknown':
                uf_dev['size'] = None
            else:
                uf_dev['size'] = int(dasdsize[:-2])
            uf_dev['id'] = device['uid']
            uf_dev['bus_id'] = device['bus-id']
            uf_dev['mpath_count'] = dasd_pim_dict[uf_dev['bus_id']]
            devs.append(uf_dev)
    return devs


def _get_dasd_pim():
    """
    Return a dictionary with bus ids of
    DASD devices as keys and number of
    paths as values
    """
    pim_dict = {}
    # execute lscss -d
    command = ['lscss', '-d']
    out, err, rc = run_command(command)
    if rc:
        raise OperationFailed('GINDASD0012E', {'err': err})
    if out:
        try:
            output_lines = out.splitlines()
            for line in output_lines[2:]:
                clms = line.split()
                pim = clms[-5]
                bus_id = clms[0]
                chipid = clms[-2] + ' ' + clms[-1]
                binaryval_pam = _hex_to_binary(pim)
                enabled_chipids = _get_paths(binaryval_pam, chipid)
                pim_dict[bus_id] = len(enabled_chipids)
        except Exception as err:
            raise OperationFailed('GINDASD0013E', {'err': err.message})
    return pim_dict


def _get_lsdasd_devs():
    """
    Executes 'lsdasd -l' command and returns
    :return: output of 'lsdasd -l' command
    """
    command = ['lsdasd', '-l']
    dasdout, err, rc = run_command(command)
    if rc:
        raise OperationFailed('GINDASD0001E', {'err': err})
    return _parse_lsdasd_output(dasdout)


def _hex_to_binary(h):
    """
    Return the actual bytes of data represented by the
    hexadecimal string specified as the parameter.
    """
    return ''.join(_byte_to_binary(ord(b)) for b in binascii.unhexlify(h))


def _byte_to_binary(n):
    """
    Converts each byte into binary value i.e. sets of 0 and 1
    """
    return ''.join(str((n & (1 << i)) and 1) for i in reversed(range(8)))


def _get_paths(mask, chipid):
    """
    method to return the enabled or installed paths of chipid.
    :param mask: the binary value for the pam or pim.
    :return: list of available or installed paths of the chipid value.
    """
    chipids = [chipid[i:i + 2] for i in range(0, len(chipid), 2)]
    chipid_paths = []
    for index, j in enumerate(mask):
        if j == '1':
            chipid_paths.append(chipids[index])
    return chipid_paths


def _parse_lsdasd_output(output):
    """
    This method parses the output of 'lsdasd' command.
    :param output: Output of the 'lsdasd' command
    :return: list containing DASD devices information
    """
    try:
        split_out = output.split('\n\n')
        out_list = []
        len_dasd = len(split_out) - 1
        for i in split_out[:len_dasd]:
            fs_dict = {}
            p = re.compile(r'^\s+(\w+)\:\s+(.+)$')
            parsed_out = i.splitlines()
            if parsed_out and '/' in parsed_out[0] and \
               len(parsed_out[0].split('/')) == 3:
                first_spl = i.splitlines()[0].split('/')
                fs_dict['bus-id'] = first_spl[0]
                fs_dict['name'] = first_spl[1]
                fs_dict['device'] = first_spl[2]
                for fs in parsed_out[1:]:
                    m = p.search(fs)
                    if not m:
                        continue
                    fs_dict[m.group(1)] = m.group(2)
                    if 'status' in fs_dict and fs_dict['status'] == 'n/f':
                        fs_dict['blksz'] = 'None'
                        fs_dict['blocks'] = 'None'
                if 'size' in fs_dict and fs_dict['size'] == '\t':
                    fs_dict['size'] = 'Unknown'
                out_list.append(fs_dict)
    except Exception:
        raise OperationFailed('GINDASD0003E')

    return out_list


def get_lsblk_keypair_out(transport=True):
    """
    Get the output of lsblk'
    :param transport: True or False for getting transport information
    :return: output of 'lsblk -Po <columns>'

    """
    if transport:
        cmd = ['lsblk', '-Pbo', 'NAME,TYPE,SIZE,TRAN']
    else:
        # Some distributions don't ship 'lsblk' with transport
        # support.
        cmd = ['lsblk', '-Pbo', 'NAME,TYPE,SIZE']

    out, err, rc = run_command(cmd)
    if rc != 0:
        raise OperationFailed('GINSD00002E', {'err': err})
    return out


def parse_lsblk_out(lsblk_out):
    """
    Parse the output of 'lsblk -Pbo'
    :param lsblk_out: output of 'lsblk -Pbo'
    :return: Dictionary containing information about
            disks on the system
    """
    try:
        out_list = lsblk_out.splitlines()

        return_dict = {}

        for disk in out_list:
            disk_info = {}
            disk_attrs = disk.split()

            disk_type = disk_attrs[1]
            if not disk_type == 'TYPE="disk"':
                continue

            if len(disk_attrs) == 4:
                disk_info['transport'] = disk_attrs[3].split('=')[1][1:-1]
            else:
                disk_info['transport'] = 'unknown'

            disk_info['size'] = int(disk_attrs[2].split('=')[1][1:-1])
            disk_info['size'] = disk_info['size'] / (1024 * 1024)
            return_dict[disk_attrs[0].split('=')[1][1:-1]] = disk_info

    except Exception as e:
        raise OperationFailed('GINSD00004E', {'err': e.message})

    return return_dict


def get_disks_by_id_out():
    """
    Execute 'ls -l /dev/disk/by-id'
    :return: Output of 'ls -l /dev/disk/by-id'
    """
    cmd = ['ls', '-l', '/dev/disk/by-id']
    out, err, rc = run_command(cmd)
    if rc != 0:
        raise OperationFailed('GINSD00001E', {'err': err})
    return out


def parse_ll_out(ll_out):
    """
    Parse the output of 'ls -l /dev/disk/by-id' command
    :param ll_out: output of 'ls -l /dev/disk/by-id'
    :return: tuple containing dictionaries. First dictionary
            contains devices as keys and the second dictionary
            contains device ids as keys
    """

    return_dict = {}
    return_id_dict = {}

    try:
        out = ll_out.splitlines()
        for line in out[1:]:
            ls_columns = line.split()
            disk_id = ls_columns[-3]

            if disk_id.startswith(
                    'ccw-') and not re.search('ccw-.+\\w{4}\\.\\w{2}$', disk_id):
                continue

            if disk_id.startswith('wwn-'):
                continue

            if disk_id.startswith('dm-name'):
                continue

            disk_name = ls_columns[-1]
            name = disk_name.split('/')[-1]

            disk_id_split = disk_id.split('-')
            skip_list = ['ccw', 'usb', 'ata']
            disk_type = disk_id_split[0]

            if disk_type not in skip_list:
                disk_id = disk_id_split[-1]

            return_dict[name] = disk_id

            if disk_id in return_id_dict:
                return_id_dict[disk_id].append(name)
            else:
                return_id_dict[disk_id] = [name]
    except Exception as e:
        raise OperationFailed('GINSD00003E', {'err': e.message})

    return return_dict, return_id_dict


def get_fc_path_elements():
    """
    Get the FC LUN ID, remote wwpn and local host adapter
    for all the 'fc' type block devices.
    :return: dictionary containing key as block device and value as
    dictionary of Host Adapter, WWPN, LUN ID
    e.g. for s390x:
         {'sda': {'wwpn': '0x5001738030bb0171',
                 'fcp_lun': '0x00df000000000000',
                 'hba_id': '0.0.7100'},
          'sdb': {'wwpn': '0x5001738030bb0171',
                  'fcp_lun': '0x41cf000000000000',
                  'hba_id': '0.0.7100'},}
    """
    fc_blk_dict = {}

    fc_devs = glob.glob(FC_PATHS)
    for path in fc_devs:
        blkdev = os.path.basename(os.path.realpath(path))

        try:
            pattern = re.compile(PATTERN_PCI)
            blk_info_dict = pattern.search(path).groupdict()
        except Exception:
            try:
                pattern = re.compile(PATTERN_CCW)
                blk_info_dict = pattern.search(path).groupdict()
            except Exception:
                # no pattern match, probably a partition (...-partN), ignore it
                continue

        fc_blk_dict[blkdev] = blk_info_dict

    return fc_blk_dict
