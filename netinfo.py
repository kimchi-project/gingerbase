#
# Project Ginger Base
#
# Copyright IBM Corp, 2016-2017
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
"""Network utilities module."""
import glob
import os
from distutils.spawn import find_executable

import ethtool
from wok.stringutils import encode_value
from wok.utils import run_command
from wok.utils import wok_log

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
    """Get all wlans declared in /sys/class/net/*/wireless.

    Returns:
        List[str]: a list with the wlans found.

    """
    return [b.split('/')[-2] for b in glob.glob(WLAN_PATH)]


def is_wlan(iface):
    """Checks if iface is a wlan.

    Args:
        iface (str): interface to be checked.

    Returns:
        bool: True if iface is a wlan, False otherwise.

    """
    return encode_value(iface) in map(encode_value, wlans())


def nics():
    """Get all nics of the host.

    This function returns every nic, including those
    that might be loaded from an usb port.

    Returns:
        List[str]: a list with the nics found.

    """
    return list(set([b.split('/')[-2] for b in glob.glob(NIC_PATH)]) -
                set(wlans()))


def is_nic(iface):
    """Checks if iface is a nic.

    Args:
        iface (str): name of the interface.

    Returns:
        bool: True if iface is a nic, False otherwise.

    """
    return encode_value(iface) in map(encode_value, nics())


def bondings():
    """Get all bondings of the host.

    Returns:
        List[str]: a list with the bonds found.

    """
    return [b.split('/')[-2] for b in glob.glob(BONDING_PATH)]


def is_bonding(iface):
    """Checks if iface is a bond.

    Args:
        iface (str): name of the interface.

    Returns:
        bool: True if iface is a bond, False otherwise.

    """
    return encode_value(iface) in map(encode_value, bondings())


def vlans():
    """Get all vlans of the host.

    Returns:
        List[str]: a list with the vlans found.

    """
    return list(
        set([b.split('/')[-1] for b in glob.glob(NET_PATH + '/*')]) &
        set([b.split('/')[-1] for b in glob.glob(PROC_NET_VLAN + '*')])
    )


def is_vlan(iface):
    """Checks if iface is a vlan.

    Args:
        iface (str): name of the interface.

    Returns:
        bool: True if iface is a vlan, False otherwise.

    """
    return encode_value(iface) in map(encode_value, vlans()) or \
        'vlan_raw_device' in _parse_interfaces_file(iface).keys()


def bridges():
    """Get all bridges of the host.

    Returns:
        List[str]: a list with the bridges found.

    """
    return list(set([b.split('/')[-2] for b in glob.glob(BRIDGE_PATH)] +
                    ovs_bridges()))


def is_bridge(iface):
    """Checks if iface is a bridge.

    Args:
        iface (str): name of the interface.

    Returns:
        bool: True if iface is a bridge, False otherwise.

    """
    return encode_value(iface) in map(encode_value, bridges())


def is_openvswitch_running():
    """Checks if the openvswitch service is running in the host.

    Returns:
        bool: True if openvswitch service is running, False otherwise.

    """
    cmd = ['systemctl', 'is-active', 'openvswitch', '--quiet']
    _, _, r_code = run_command(cmd, silent=True)
    return r_code == 0


def ovs_bridges():
    """Get the OVS Bridges of the host.

    In some distributions, like Fedora, the files bridge and brif are
    not created under /sys/class/net/<ovsbridge> for OVS bridges.
    These specific functions allows one to differentiate OVS bridges
    from other types of bridges.

    Returns:
        List[str]: a list with the OVS bridges found.

    """
    if not is_openvswitch_running():
        return []

    ovs_cmd = find_executable('ovs-vsctl')

    # openvswitch not installed: there is no OVS bridge configured
    if ovs_cmd is None:
        return []

    out, _, r_code = run_command([ovs_cmd, 'list-br'], silent=True)
    if r_code != 0:
        return []

    return [x.strip() for x in out.rstrip('\n').split('\n') if x.strip()]


def is_ovs_bridge(iface):
    """Checks if iface is an OVS bridge.

    In some distributions, like Fedora, the files bridge and brif are
    not created under /sys/class/net/<ovsbridge> for OVS bridges.
    These specific functions allows one to differentiate OVS bridges
    from other types of bridges.

    Args:
        iface (str): name of the interface.

    Returns:
        bool: True if iface is an OVS bridge, False otherwise.

    """
    return iface in ovs_bridges()


def ovs_bridge_ports(ovsbr):
    """Get the ports of a OVS bridge.

    In some distributions, like Fedora, the files bridge and brif are
    not created under /sys/class/net/<ovsbridge> for OVS bridges.
    These specific functions allows one to differentiate OVS bridges
    from other types of bridges.

    Args:
        ovsbr (str): name of the OVS bridge

    Returns:
        List[str]: a list with the ports of this bridge.

    """
    if not is_openvswitch_running():
        return []

    ovs_cmd = find_executable('ovs-vsctl')

    # openvswitch not installed: there is no OVS bridge configured
    if ovs_cmd is None:
        return []

    out, _, r_code = run_command([ovs_cmd, 'list-ports', ovsbr], silent=True)
    if r_code != 0:
        return []

    return [x.strip() for x in out.rstrip('\n').split('\n') if x.strip()]


def all_interfaces():
    """Returns all interfaces of the host.

    Returns:
        List[str]: a list with all interfaces of the host.

    """
    return [d.rsplit('/', 1)[-1] for d in glob.glob(NET_PATH + '/*')]


def slaves(bonding):
    """Get all slaves from a bonding.

    Args:
        bonding (str): the name of the bond.

    Returns:
        List[str]: a list with all slaves.

    """
    with open(BONDING_SLAVES % bonding) as bonding_file:
        res = bonding_file.readline().split()
    return res


def ports(bridge):
    """Get all ports from a bridge.

    Args:
        bridge (str): the name of the OVS bridge.

    Returns:
        List[str]: a list with all ports.

    """
    if bridge in ovs_bridges():
        return ovs_bridge_ports(bridge)

    ports = []
    if os.path.exists(BRIDGE_PORTS % bridge):
        ports = os.listdir(BRIDGE_PORTS % bridge)

    if len(ports) == 0:
        bridge_data = _parse_interfaces_file(bridge)
        return bridge_data.get('bridge_ports', [])
    else:
        return ports


def _parse_interfaces_file(iface):
    ifaces = []

    try:
        content = open('/etc/network/interfaces').readlines()
        for line in content:
            if line.startswith('iface'):
                ifaces.append({'iface': line.split()[1],
                               'index': content.index(line)})
    except IOError:
        wok_log.debug('Unable to get bridge information from '
                      '/etc/network/interfaces')
        return {}

    index = next_index = None
    for data in ifaces:
        if data['iface'] == iface:
            index = data['index']
            next_elem = ifaces.index(data) + 1
            if next_elem > len(ifaces) - 1:
                next_index = len(content)
            else:
                next_index = ifaces[ifaces.index(data) + 1]['index']
            break

    if index is None or next_index is None:
        return {}

    result = {}
    iface_data = content[index + 1:next_index]
    for item in iface_data:
        data = item.split()
        result[data[0]] = data[1:]

    return result


def is_brport(nic):
    """Checks if nic is a port of a bridge.

    Args:
        iface (str): name of the interface.

    Returns:
        bool: True if iface is a port of a bridge, False otherwise.

    """
    ovs_brports = []

    for ovsbr in ovs_bridges():
        ovs_brports += ovs_bridge_ports(ovsbr)

    return os.path.exists(NET_BRPORT % nic) or nic in ovs_brports


def is_bondlave(nic):
    """Checks if nic is a bond slave.

    Args:
        iface (str): name of the interface.

    Returns:
        bool: True if iface is a bond slave, False otherwise.

    """
    return os.path.exists(NET_MASTER % nic)


def operstate(dev):
    """Get the operstate status of a device.

    Args:
        dev (str): name of the device.

    Returns:
        str: "up" or "down"

    """
    def operstate_status(dev):
        """"Read operstate file in the filesystem."""
        # try to read interface operstate (link) status
        try:
            with open(NET_STATE % dev) as dev_file:
                return dev_file.readline().strip()
        # when IOError is raised, interface is down
        except IOError:
            return 'down'

    op_status = operstate_status(dev)
    return 'up' if op_status == 'up' else 'down'


def link_detected(dev):
    """Get the carrier status of a device.

    Args:
        dev (str): name of the device.

    Returns:
        str: "yes" or "no" or "n/a"

    """
    # try to read interface carrier (link) status
    try:
        with open(NET_CARRIER_STATE % dev) as dev_file:
            carrier = dev_file.readline().strip()
    # when IOError is raised, interface is down
    except IOError:
        return 'n/a'

    # if value is 1, interface up with cable connected
    # 0 corresponds to interface up with cable disconnected
    return 'yes' if carrier == '1' else 'no'


def macaddr(dev):
    """Get the mac address of a device.

    Args:
        dev (str): name of the device.

    Returns:
        str: the mac address of the device.

    """

    try:
        with open(MAC_ADDRESS % dev) as dev_file:
            hwaddr = dev_file.readline().strip()
            return hwaddr
    except IOError:
        return 'n/a'


def get_vlan_device(vlan):
    """ Return the device of the given VLAN.

    Args:
        vlan (str): the vlan name.

    Returns:
        str: the device of the VLAN.

    """
    dev = None

    if os.path.exists(PROC_NET_VLAN + vlan):
        with open(PROC_NET_VLAN + vlan) as vlan_file:
            for line in vlan_file:
                if 'Device:' in line:
                    dummy, dev = line.split()
                    break

    if dev is None:
        dev_info = _parse_interfaces_file(vlan).get('vlan_raw_device', None)
        if dev_info:
            return dev_info[0]
    else:
        return dev


def get_bridge_port_device(bridge):
    """Return the nics list that belongs to a port of 'bridge'.

    Args:
        bridge (str): the bridge name.

    Returns:
        List[str]: the nic list.

    """
    #   br  --- v  --- bond --- nic1
    if encode_value(bridge) not in map(encode_value, bridges()):
        raise ValueError('unknown bridge %s' % bridge)
    nics_list = []
    for port in ports(bridge):
        if encode_value(port) in map(encode_value, vlans()):
            device = get_vlan_device(port)
            if encode_value(device) in map(encode_value, bondings()):
                nics_list.extend(slaves(device))
            else:
                nics_list.append(device)
        if encode_value(port) in map(encode_value, bondings()):
            nics_list.extend(slaves(port))
        else:
            nics_list.append(port)
    return nics_list


def aggregated_bridges():
    """Get the list of aggregated bridges of the host.

    Returns:
        List[str]: the aggregated bridges list.

    """
    return [bridge for bridge in bridges() if
            (set(get_bridge_port_device(bridge)) & set(nics()))]


def bare_nics():
    """Get the list of bare nics of the host.

    A nic is called bare when it is not a port of a bridge
    or a slave of bond.

    Returns:
        List[str]: the list of bare nics of the host.

    """
    return [nic for nic in nics() if not (is_brport(nic) or is_bondlave(nic))]


def is_bare_nic(iface):
    """Checks if iface is a bare nic.

    Args:
        iface (str): name of the interface.

    Returns:
        bool: True if iface is a bare nic, False otherwise.

    """
    return encode_value(iface) in map(encode_value, bare_nics())


#  The nic will not be exposed when it is a port of a bridge or
#  a slave of bond.
#  The bridge will not be exposed when all it's port are tap.
def all_favored_interfaces():
    """Get the list of all favored interfaces of the host.

    The nic will not be exposed when it is a port of a bridge or
    a slave of bond. The bridge will not be exposed when all its
    port are tap.

    Returns:
        List[str]: the list of favored interfaces.

   """
    return aggregated_bridges() + bare_nics() + bondings()


def get_interface_kernel_module(iface):
    """Get the kernel module that loaded the interface.

    Args:
        iface (str): the interface name.

    Returns:
        str: the kernel module that loaded iface.

    """
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
        bus_id = os.readlink(link_path).split('/')[-1]
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
    out, err, r_code = run_command(lspci_cmd)

    if r_code == 0 and 'Virtual Function' in out:
        return 'virtual'

    if r_code != 0:
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
    """Get the interface type of iface.

    Types supported: nic, bonding, bridge, vlan. If the type
    can't be verified, 'unknown' is returned.

    Args:
        iface (str): the interface name.

    Returns:
        str: the interface type.

    """
    try:
        if is_nic(iface):
            return 'nic'
        if is_bonding(iface):
            return 'bonding'
        if is_bridge(iface):
            return 'bridge'
        if is_vlan(iface):
            return 'vlan'
        return 'unknown'
    except IOError:
        return 'unknown'


def get_interface_info(iface):
    """Returns information about the interface iface.

    Args:
        iface (str): the interface name.

    Returns:
        dict: a dict containing the interface info. Format:
            {
                'device': (str),
                'name': (str),
                'type': (str),
                'status': (str),
                'link_detected': (str),
                'ipaddr': (str),
                'netmask': (str),
                'macaddr': (str),
                'module': (str),
                'nic_type': (str)
            }

    """
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
    nic_type = 'N/A' if iface_type != 'nic' else get_nic_type(iface, kernel_module)

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


def get_interfaces_with_modules(modules):
    """Returns all interfaces loaded with the 'modules' list.

    Args:
        modules (List[str]): a list of modules.

    Returns:
        List[str]: a list with all interfaces loaded with the
            modules contained in the 'modules' list.

    """
    return [iface for iface in all_interfaces() if
            get_interface_kernel_module(iface) in modules]


def is_interface_rdma_capable(interface):
    """Checks if 'interface' is RDMA capable.

    Current implementation only supports RDMA in ConnectX-4
    cards.

    Args:
        interface (str): the name of the interface.


    Returns:
        bool: True if interface is RDMA capable. False otherwise.

    """
    rdma_modules = ['mlx5_core', 'mlx5-core']
    if get_interface_kernel_module(interface) in rdma_modules:
        return True
    return False


def is_rdma_service_enabled():
    """Checks if any RDMA service is enabled in the host.

    The RDMA services considered in this function are 'rdma'
    and 'openibd'.

    Returns:
        bool: True if any RDMA service is enabled. False otherwise.

    """
    for rdma_service in ['rdma', 'openibd']:
        cmd = ['systemctl', 'is-active', rdma_service, '--quiet']
        _, _, r_code = run_command(cmd, silent=True)
        if r_code == 0:
            return True
    return False


def is_rdma_enabled(interface):
    """Check if the interface has RDMA enabled at the moment.

    Note that this depends on whether the interface has RDMA
    support and if there is a RDMA service running in the host.

    Args:
        interface (str): the name of the interface.

    Returns:
        bool: True if RDMA is enabled in 'interface', False otherwise.

    """
    return is_interface_rdma_capable(interface) and is_rdma_service_enabled()


def get_rdma_enabled_interfaces():
    """Get a list of all RDMA capable interfaces in the host.

    Note that this depends on whether the interfaces have RDMA
    support and if there is a RDMA service running in the host.

    Returns:
        List[str]: a list of all RDMA interfaces in the host.

    """
    if not is_rdma_service_enabled():
        return []

    return [iface for iface in all_interfaces() if
            is_interface_rdma_capable(iface)]
