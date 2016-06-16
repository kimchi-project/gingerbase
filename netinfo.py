#
# Project Ginger Base
#
# Copyright IBM Corp, 2016
#
# Code derived from Project Ginger and Kimchi
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

import ethtool
import glob
import os

from distutils.spawn import find_executable
from wok.utils import encode_value, run_command, wok_log

NET_PATH = '/sys/class/net'
NIC_PATH = '/sys/class/net/*/device'
BRIDGE_PATH = '/sys/class/net/*/bridge'
BONDING_PATH = '/sys/class/net/*/bonding'
WLAN_PATH = '/sys/class/net/*/wireless'
NET_BRPORT = '/sys/class/net/%s/brport'
NET_MASTER = '/sys/class/net/%s/master'
NET_STATE = '/sys/class/net/%s/operstate'
NET_CARRIER_STATE = '/sys/class/net/%s/carrier'
PROC_NET_VLAN = '/proc/net/vlan/'
BONDING_SLAVES = '/sys/class/net/%s/bonding/slaves'
BRIDGE_PORTS = '/sys/class/net/%s/brif'
MAC_ADDRESS = '/sys/class/net/%s/address'
KERNEL_MODULE_LINK = '/sys/class/net/%s/device/driver/module'


def wlans():
    return [b.split('/')[-2] for b in glob.glob(WLAN_PATH)]


def is_wlan(iface):
    return encode_value(iface) in map(encode_value, wlans())


# FIXME if we do not want to list usb nic
def nics():
    return list(set([b.split('/')[-2] for b in glob.glob(NIC_PATH)]) -
                set(wlans()))


def is_nic(iface):
    return encode_value(iface) in map(encode_value, nics())


def bondings():
    return [b.split('/')[-2] for b in glob.glob(BONDING_PATH)]


def is_bonding(iface):
    return encode_value(iface) in map(encode_value, bondings())


def vlans():
    return list(set([b.split('/')[-1]
                     for b in glob.glob(NET_PATH + '/*')]) &
                set([b.split('/')[-1]
                     for b in glob.glob(PROC_NET_VLAN + '*')]))


def is_vlan(iface):
    return encode_value(iface) in map(encode_value, vlans())


def bridges():
    return list(set([b.split('/')[-2] for b in glob.glob(BRIDGE_PATH)] +
                    ovs_bridges()))


def is_bridge(iface):
    return encode_value(iface) in map(encode_value, bridges())


def is_openvswitch_running():
    cmd = ['systemctl', 'is-active', 'openvswitch', '--quiet']
    _, _, rc = run_command(cmd, silent=True)
    return rc == 0


# In some distributions, like Fedora, the files bridge and brif are not created
# under /sys/class/net/<ovsbridge> for OVS bridges. These specific functions
# allows one to differentiate OVS bridges from other types of bridges.
def ovs_bridges():
    if not is_openvswitch_running():
        return []

    ovs_cmd = find_executable("ovs-vsctl")

    # openvswitch not installed: there is no OVS bridge configured
    if ovs_cmd is None:
        return []

    out, error, rc = run_command([ovs_cmd, 'list-br'], silent=True)
    if rc != 0:
        return []

    return [x.strip() for x in out.rstrip('\n').split('\n') if x.strip()]


def is_ovs_bridge(iface):
    return iface in ovs_bridges()


def ovs_bridge_ports(ovsbr):
    if not is_openvswitch_running():
        return []

    ovs_cmd = find_executable("ovs-vsctl")

    # openvswitch not installed: there is no OVS bridge configured
    if ovs_cmd is None:
        return []

    out, error, rc = run_command([ovs_cmd, 'list-ports', ovsbr], silent=True)
    if rc != 0:
        return []

    return [x.strip() for x in out.rstrip('\n').split('\n') if x.strip()]


def all_interfaces():
    return [d.rsplit("/", 1)[-1] for d in glob.glob(NET_PATH + '/*')]


def slaves(bonding):
    with open(BONDING_SLAVES % bonding) as bonding_file:
        res = bonding_file.readline().split()
    return res


def ports(bridge):
    if bridge in ovs_bridges():
        return ovs_bridge_ports(bridge)

    return os.listdir(BRIDGE_PORTS % bridge)


def is_brport(nic):
    ovs_brports = []

    for ovsbr in ovs_bridges():
        ovs_brports += ovs_bridge_ports(ovsbr)

    return os.path.exists(NET_BRPORT % nic) or nic in ovs_brports


def is_bondlave(nic):
    return os.path.exists(NET_MASTER % nic)


def operstate(dev):

    def operstate_status(dev):
        # try to read interface operstate (link) status
        try:
            with open(NET_STATE % dev) as dev_file:
                return dev_file.readline().strip()
        # when IOError is raised, interface is down
        except IOError:
            return "down"

    op_status = operstate_status(dev)
    return "up" if op_status == "up" else "down"


def link_detected(dev):
    # try to read interface carrier (link) status
    try:
        with open(NET_CARRIER_STATE % dev) as dev_file:
            carrier = dev_file.readline().strip()
    # when IOError is raised, interface is down
    except IOError:
        return "n/a"

    # if value is 1, interface up with cable connected
    # 0 corresponds to interface up with cable disconnected
    return "yes" if carrier == '1' else "no"


def macaddr(dev):
    try:
        with open(MAC_ADDRESS % dev) as dev_file:
            hwaddr = dev_file.readline().strip()
            return hwaddr
    except IOError:
        return "n/a"


def get_vlan_device(vlan):
    """ Return the device of the given VLAN. """
    dev = None

    if os.path.exists(PROC_NET_VLAN + vlan):
        with open(PROC_NET_VLAN + vlan) as vlan_file:
            for line in vlan_file:
                if "Device:" in line:
                    dummy, dev = line.split()
                    break
    return dev


def get_bridge_port_device(bridge):
    """Return the nics list that belongs to bridge."""
    #   br  --- v  --- bond --- nic1
    if encode_value(bridge) not in map(encode_value, bridges()):
        raise ValueError('unknown bridge %s' % bridge)
    nics = []
    for port in ports(bridge):
        if encode_value(port) in map(encode_value, vlans()):
            device = get_vlan_device(port)
            if encode_value(device) in map(encode_value, bondings()):
                nics.extend(slaves(device))
            else:
                nics.append(device)
        if encode_value(port) in map(encode_value, bondings()):
            nics.extend(slaves(port))
        else:
            nics.append(port)
    return nics


def aggregated_bridges():
    return [bridge for bridge in bridges() if
            (set(get_bridge_port_device(bridge)) & set(nics()))]


def bare_nics():
    "The nic is not a port of a bridge or a slave of bond."
    return [nic for nic in nics() if not (is_brport(nic) or is_bondlave(nic))]


def is_bare_nic(iface):
    return encode_value(iface) in map(encode_value, bare_nics())


#  The nic will not be exposed when it is a port of a bridge or
#  a slave of bond.
#  The bridge will not be exposed when all it's port are tap.
def all_favored_interfaces():
    return aggregated_bridges() + bare_nics() + bondings()


def get_interface_kernel_module(iface):
    link_path = KERNEL_MODULE_LINK % iface
    try:
        link_target = os.readlink(link_path)
    except OSError:
        return 'unknown'
    module = link_target.split('/')[-1]
    return module


def get_mlx5_nic_bus_id(mlx5_iface):
    """Reads the /sys filesystem to retrieve the bus id
    of a given interface loaded by the mlx5_core driver.

    Args:
        mlx5_iface (str): interface loaded by the mlx5_core driver.

    Returns:
        str: the PCI bus id for mlx5_iface. If an error occurs,
            'unknown' is returned.

    """
    try:
        link_path = '/sys/class/net/%s/device' % mlx5_iface
        bus_id = os.readlink(link_path).split("/")[-1]
    except OSError:
        bus_id = 'unknown'

    return bus_id


def get_mlx5_nic_type(mlx5_iface):
    """Checks lspci output to see if mlx5_iface is a physical or
    virtual nic interface.

    This is the lspci output this function is expecting for a mlx5 virtual
    nic interface:

    'Ethernet controller: Mellanox Technologies MT27700 Family
     [ConnectX-4 Virtual Function]'

    Verification will be done by checking for the 'Virtual Function'
    string in the output. Any other lspci output format or any other
    error will make this function return the default value 'physical'.

    Args:
        mlx5_iface (str): interface loaded by the mlx5_core driver.

    Returns:
        str: 'virtual' if mlx5_iface is a virtual function/nic,
            'physical' otherwise.

    """
    bus_id = get_mlx5_nic_bus_id(mlx5_iface)

    lspci_cmd = ['lspci', '-s', bus_id]
    out, err, rc = run_command(lspci_cmd)

    if rc == 0 and 'Virtual Function' in out:
        return 'virtual'

    if rc != 0:
        wok_log.error('Error while getting nic type of '
                      'interface: %s' % err)

    return 'physical'


def get_nic_type(iface, iface_kernel_mod=None):
    """Get the nic type for an given nic interface iface.

    This function will return 'physical' for any iface that
    is not loaded by mlx5_core driver. For mlx5_cards a
    verification will be made to see if iface is a virtual
    function (VF).

    Args:
        iface (str): a nic interface.
        iface_kernel_mod(Optional[str]): the kernel driver that
            loaded this interface.

    Returns:
        (str): 'physical' or 'virtual'.

    """
    if iface_kernel_mod is None:
        iface_kernel_mod = get_interface_kernel_module(iface)

    if iface_kernel_mod not in ['mlx5_core', 'mlx5-core']:
        return 'physical'

    return get_mlx5_nic_type(iface)


def get_interface_type(iface):
    # FIXME if we want to get more device type
    # just support nic, bridge, bondings and vlan, for we just
    # want to expose this 4 kinds of interface
    try:
        if is_nic(iface):
            return "nic"
        if is_bonding(iface):
            return "bonding"
        if is_bridge(iface):
            return "bridge"
        if is_vlan(iface):
            return "vlan"
        return 'unknown'
    except IOError:
        return 'unknown'


def get_interface_info(iface):
    if encode_value(iface) not in map(encode_value, ethtool.get_devices()):
        raise ValueError('unknown interface: %s' % iface)

    ipaddr = ''
    netmask = ''
    try:
        ipaddr = ethtool.get_ipaddr(encode_value(iface))
        netmask = ethtool.get_netmask(encode_value(iface))
    except IOError:
        pass

    kernel_module = get_interface_kernel_module(iface)
    iface_type = get_interface_type(iface)
    nic_type = 'N/A' if iface_type is not 'nic' \
        else get_nic_type(iface, kernel_module)

    return {'device': iface,
            'name': iface,
            'type': iface_type,
            'status': operstate(iface),
            'link_detected': link_detected(iface),
            'ipaddr': ipaddr,
            'netmask': netmask,
            'macaddr': macaddr(iface),
            'module': kernel_module,
            'nic_type': nic_type}


def get_interfaces_loaded_with_modules(modules):
    return [iface for iface in all_interfaces() if
            get_interface_kernel_module(iface) in modules]


def is_interface_rdma_capable(interface):
    rdma_modules = ['mlx5_core', 'mlx5-core']
    if get_interface_kernel_module(interface) in rdma_modules:
        return True
    return False


def is_rdma_service_enabled():
    for rdma_service in ['rdma', 'openibd']:
        cmd = ['systemctl', 'is-active', rdma_service, '--quiet']
        _, _, rc = run_command(cmd, silent=True)
        if rc == 0:
            return True
    return False


def is_rdma_enabled(interface):
    return is_interface_rdma_capable(interface) and is_rdma_service_enabled()


def get_rdma_enabled_interfaces():
    if not is_rdma_service_enabled():
        return []

    return [iface for iface in all_interfaces() if
            is_interface_rdma_capable(iface)]
