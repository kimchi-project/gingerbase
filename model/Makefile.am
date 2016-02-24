#
# Ginger Base
#
# Copyright IBM Corp, 2015
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

model_PYTHON = $(filter-out config.py, $(wildcard *.py))

nodist_model_PYTHON = config.py

EXTRA_DIST = config.py.in

modeldir = $(pythondir)/wok/plugins/gingerbase/model

install-data-local:
	$(MKDIR_P) $(DESTDIR)$(modeldir)

do_substitution = \
	sed -e 's,[@]gingerbaseversion[@],$(PACKAGE_VERSION),g' \
	-e 's,[@]gingerbaserelease[@],$(PACKAGE_RELEASE),g'

config.py: config.py.in Makefile
	$(do_substitution) < $(srcdir)/config.py.in > config.py

BUILT_SOURCES = config.py
CLEANFILES = config.py
	$(models_PYTHON:%.py=%.pyc) \
	$(NULL)
