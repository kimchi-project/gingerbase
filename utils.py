#
# Project Kimchi
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
#

import base64
import contextlib
import os
import urllib2
from httplib import HTTPConnection, HTTPException, HTTPSConnection
from urlparse import urlparse

from wok.exception import InvalidParameter


MAX_REDIRECTION_ALLOWED = 5


def check_url_path(path, redirected=0):
    if redirected > MAX_REDIRECTION_ALLOWED:
        return False
    try:
        code = ''
        parse_result = urlparse(path)
        headers = {}
        server_name = parse_result.hostname
        if (parse_result.scheme in ['https', 'ftp']) and \
           (parse_result.username and parse_result.password):
            # Yum accepts http urls with user and password credentials. Handle
            # them and avoid access test errors
            credential = parse_result.username + ':' + parse_result.password
            headers = {'Authorization': 'Basic %s' %
                       base64.b64encode(credential)}
        urlpath = parse_result.path
        if not urlpath:
            # Just a server, as with a repo.
            with contextlib.closing(urllib2.urlopen(path)) as res:
                code = res.getcode()
        else:
            # socket.gaierror could be raised,
            #   which is a child class of IOError
            if headers:
                conn = HTTPSConnection(server_name, timeout=15)
            else:
                conn = HTTPConnection(server_name, timeout=15)
            # Don't try to get the whole file:
            conn.request('HEAD', urlpath, headers=headers)
            response = conn.getresponse()
            code = response.status
            conn.close()
        if code == 200:
            return True
        elif code == 301 or code == 302:
            for header in response.getheaders():
                if header[0] == 'location':
                    return check_url_path(header[1], redirected+1)
        else:
            return False
    except (urllib2.URLError, HTTPException, IOError, ValueError):
        return False
    return True


def validate_repo_url(url):
    url_parts = url.split('://')  # [0] = prefix, [1] = rest of URL

    if url_parts[0] == '':
        raise InvalidParameter("GGBREPOS0002E")

    if url_parts[0] in ['http', 'https', 'ftp']:
        if not check_url_path(url):
            raise InvalidParameter("GGBUTILS0001E", {'url': url})
    elif url_parts[0] == 'file':
        if not os.path.exists(url_parts[1]):
            raise InvalidParameter("GGBUTILS0001E", {'url': url})
    else:
        raise InvalidParameter("GGBREPOS0002E")
