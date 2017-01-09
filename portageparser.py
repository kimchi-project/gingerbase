#
# Project Ginger Base
#
# Copyright IBM Corp, 2017
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

from wok.utils import run_command


def _filter_lines_checkupdate_output(output):
    """returns lines starting with ["""
    return [line for line in output.split('\n')
            if line.startswith('[')]


def _get_portage_checkupdate_output():
    """simple formatted output of outdated packages"""
    cmd = ['emerge', '-up', '--quiet', '--nospinner', '@world']
    out, error, return_code = run_command(cmd, silent=True)
    if return_code == 1:
        return ''
    return out


def packages_list_update(checkupdate_output=None):
    """
    Returns a list of packages eligible to be updated.
    """
    if checkupdate_output is None:
        checkupdate_output = _get_portage_checkupdate_output()
    filtered_output = _filter_lines_checkupdate_output(checkupdate_output)

    packages = []
    names = []
    for line in filtered_output:
        arch = ''
        line = line.split(']', 1)
        name = line[1].strip().split()[0]
        version = ''
        repo = ''
        if name not in names:
            names.append(name)
            pkg = {'package_name': name, 'arch': arch, 'version': version,
                   'repository': repo}
        packages.append(pkg)
    return packages


def package_deps(pkg_name):
    """
    dependencies for a given package.
    make sure pkg_name is a full atom (grp/pkg-ver)
    """
    cmd = ['equery', '-C', '-q', 'depgraph', '=%s' % pkg_name]
    out, error, return_code = run_command(cmd, silent=True)
    if return_code == 1:
        return []
    packages = set()
    for line in out.split('\n')[2:]:
        elems = line.split()
        if elems:
            packages.add(elems[-1].strip())

    return list(packages)


def package_info(pkg_name):
    """
    dict holding info about package.
    no meaningful way to return arch, version, repo in gentoo
    therefore only pkg_name is returned, equery holds other
    metafacts, also interesting?
    """
    cmd = ['equery', '-C', '-q', 'meta', pkg_name]
    out, error, return_code = run_command(cmd, silent=True)
    if return_code == 1:
        return None
    return {'package_name': pkg_name, 'arch': '',
            'version': '', 'repository': ''}


if __name__ == '__main__':
    print(packages_list_update())
    print(package_deps('www-servers/nginx-1.11.6'))
    print(package_info('www-servers/nginx-1.11.6'))
