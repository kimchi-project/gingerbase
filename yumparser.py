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

import glob

from os import listdir
from os.path import isfile, splitext, basename

from wok.utils import run_command

try:
    import rpm
except ImportError:
    pass


class YumRepoObject(object):

    def __init__(self, repo_id, repofile):
        self.repo_id = repo_id
        self.name = None
        self.baseurl = None
        self.enabled = True
        self.gpgcheck = True
        self.gpgkey = None
        self.metalink = None
        self.mirrorlist = None
        self.repofile = repofile
        self.string_attrs = ['baseurl', 'gpgkey', 'name',
                             'metalink', 'mirrorlist']
        self.boolean_attrs = ['enabled', 'gpgcheck']

    def set_attribute(self, key, strvalue):
        if key in self.string_attrs:
            setattr(self, key, strvalue)
        elif key in self.boolean_attrs:
            setattr(self, key, (strvalue == '1'))

    def get_attribute_str(self, key):
        if key not in self.get_attributes():
            return None

        if key in self.boolean_attrs:
            str_value = '1' if getattr(self, key) is True else '0'
        else:
            str_value = getattr(self, key)

        if str_value is None:
            return None

        return key + '=' + str_value

    def get_attributes(self):
        return self.string_attrs + self.boolean_attrs

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def __str__(self):
        str_obj = '[' + self.repo_id + ']' + '\n'
        for key in self.get_attributes():
            if self.get_attribute_str(key) is not None:
                str_obj += self.get_attribute_str(key) + '\n'
        return str_obj


def get_repo_files():
    def _is_repository_file(f):
        _, f_extension = splitext(f)
        return isfile(f) and (f_extension == '.repo')

    YUM_REPO_DIR = '/etc/yum.repos.d'
    return [YUM_REPO_DIR+'/'+f for f in listdir(YUM_REPO_DIR)
            if _is_repository_file(YUM_REPO_DIR+'/'+f)]


def _ignore_line_repo_file(line):
    return line.startswith("#") or '=' not in line


def _get_repos_from_file(repo_file):
    repos_from_file = {}
    current_repo = None
    current_repo_id = None
    with open(repo_file) as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith("["):
                if current_repo is not None:
                    repos_from_file[current_repo_id] = current_repo
                current_repo_id = line.strip('[]')
                current_repo = YumRepoObject(current_repo_id, repo_file)
                continue
            if _ignore_line_repo_file(line):
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            current_repo.set_attribute(key, value)

        # add the last repo from file.
        if current_repo is not None:
            repos_from_file[current_repo_id] = current_repo

    return repos_from_file


def get_yum_repositories():
    repo_files = get_repo_files()
    repos = {}
    for yum_repo in repo_files:
        repos.update(_get_repos_from_file(yum_repo))

    return repos


def _retrieve_repo_line_index(data, repo):
    repo_entry = '[' + repo.repo_id + ']\n'
    try:
        repo_index = data.index(repo_entry)
    except:
        return None
    return repo_index


def _update_repo_file_data(data, repo, repo_index):
    remaining_repo_attrs = repo.get_attributes()

    for i in range(repo_index + 1, len(data)):
        line = data[i].strip()
        if line.startswith('['):
            break
        if _ignore_line_repo_file(line):
            continue
        key, _ = line.split('=', 1)
        key = key.strip()
        attr_str = repo.get_attribute_str(key)
        if attr_str is None:
            continue
        remaining_repo_attrs.remove(key)
        data[i] = attr_str + '\n'

    for attr in remaining_repo_attrs:
        attr_str = repo.get_attribute_str(attr)
        if attr_str is None:
            continue
        data.insert(repo_index+1, attr_str + '\n')

    return data


def write_repo_to_file(repo):
    with open(repo.repofile) as f:
        data = f.readlines()

    repo_index = _retrieve_repo_line_index(data, repo)
    if repo_index is None:
        return

    data = _update_repo_file_data(data, repo, repo_index)

    with open(repo.repofile, 'w') as f:
        f.writelines(data)


def _get_last_line_repo(data, repo_index):
    stop_delete_index = None
    for i in range(repo_index+1, len(data)):
        line = data[i].strip()
        if line.startswith('['):
            stop_delete_index = i - 1
            break
    if stop_delete_index is None:
        stop_delete_index = len(data) - 1

    return stop_delete_index


def _remove_repo_file_data(data, repo_index):
    last_line_repo = _get_last_line_repo(data, repo_index)
    for i in range(last_line_repo, repo_index - 1, -1):
        data.pop(i)
    return data


def delete_repo_from_file(repo):
    with open(repo.repofile) as f:
        data = f.readlines()

    repo_index = _retrieve_repo_line_index(data, repo)
    if repo_index is None:
        return

    data = _remove_repo_file_data(data, repo_index)

    with open(repo.repofile, 'w') as f:
        f.writelines(data)


def _get_releasever():
    release_file = glob.glob('/etc/*-release')[0]
    transaction = rpm.TransactionSet()
    match_iter = transaction.dbMatch('basenames', release_file)

    ret = '%releasever'
    try:
        ret = match_iter.next()['version']

    except StopIteration:
        pass

    return ret


def _get_basearch():
    cmd = ['uname', '-i']
    out, error, return_code = run_command(cmd)
    return out.strip('"\n')


def _get_all_yum_vars():
    variables = {}

    def _get_var_content(varfile):
        with open(varfile) as f:
            variables[basename(varfile)] = f.read().strip('\n')

    map(lambda vfile:
        _get_var_content(vfile),
        glob.glob('/etc/yum/vars/*'))

    return variables


def _expand_variables(stringvar, split_char=' '):
    yum_variables = _get_all_yum_vars()
    yum_variables['releasever'] = _get_releasever()
    yum_variables['basearch'] = _get_basearch()

    name_vars = [var for var in stringvar.split(split_char)
                 if var.startswith('$') and var.strip('$') in yum_variables]

    return reduce(lambda nm, var:
                  nm.replace(var, yum_variables[var.strip('$')]),
                  name_vars,
                  stringvar)


def get_display_name(name):
    if not name or '$' not in name:
        return name

    return _expand_variables(name)


def get_expanded_url(url):
    url_path = url.split('://')
    if len(url_path) != 2 or '$' not in url:
        return url

    return _expand_variables(url, '/')


def _include_line_checkupdate_output(line):
    tokens = line.split()

    if len(tokens) != 3:
        return False

    if '.' not in tokens[0]:
        return False

    return True


def _ignore_obsoleting_packages_in(output):
    out = ''
    for l in output.split('\n'):
        if 'Obsoleting ' in l:
            break
        out += l + '\n'
    return out


def _filter_lines_checkupdate_output(output):
    if output is None:
        return []

    output = _ignore_obsoleting_packages_in(output)

    out = [l for l in output.split('\n')
           if _include_line_checkupdate_output(l)]
    return out


def _get_yum_checkupdate_output():
    cmd = ['yum', 'check-update', '-d0']
    out, error, return_code = run_command(cmd, silent=True)
    if return_code == 1:
        return None
    return out


def get_yum_packages_list_update(checkupdate_output=None):
    """
    Returns a list of packages eligible to be updated.
    """
    if checkupdate_output is None:
        checkupdate_output = _get_yum_checkupdate_output()
    filtered_output = _filter_lines_checkupdate_output(checkupdate_output)

    packages = []
    for line in filtered_output:
        line = line.split()
        name, arch = line[0].rsplit('.', 1)
        packages.append(name)
    packages = list(set(packages))
    return packages


def _get_package_info(pkg_name, output=None):
    if output is None:
        return {}

    package = {}
    pkg_dep = []
    for line in output:
        line = line.split()
        if len(line) < 5:
            continue
        if line[0] == pkg_name:
            package = {'package_name': line[0], 'arch': line[1],
                       'version': line[2], 'repository': line[3]}
        else:
            # it's a dependency
            pkg_dep.append(line[0])
    package['depends'] = list(set(pkg_dep))
    return package


def get_yum_package_info(pkg_name):
    """
    Returns package information as a dictionary.
    """
    cmd = ['yum', '-v', '--assumeno', 'update', pkg_name]
    out, error, returncode = run_command(cmd, silent=True)
    if returncode != 1:
        return []

    # Get the end of the output and parse it
    out = out.split('\n')
    out = out[out.index('Dependencies Resolved')+1:]
    # Remove the useless part of the output
    out = out[5:out.index('Transaction Summary')]

    return _get_package_info(pkg_name, out)


def get_dnf_package_info(pkg_name):
    """
    Returns package information as a dictionary.
    """
    cmd = ['dnf', '-v', '--assumeno', 'update', pkg_name]
    out, error, returncode = run_command(cmd, silent=True)
    if returncode != 1:
        return []

    # Get the end of the output and parse it
    out = out.split('\n')
    out = out[out.index('Dependencies resolved.')+1:]
    # Remove the useless part of the output
    out = out[3:out.index('Transaction Summary')]

    return _get_package_info(pkg_name, out)
