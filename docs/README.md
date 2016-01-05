Ginger Base Plugin
==============

Ginger Base is an open source base host management plugin for Wok
(Webserver Originated from Kimchi), that provides an intuitive web panel with
common tools for configuring and managing the Linux systems.

Wok is a cherrypy-based web framework with HTML5 support that is extended by
plugins which expose functionality through REST APIs.

The current features of Base Host Management of Linux system include:
    + Shutdown, Restart, Connect
    + Basic Information
    + System Statistics
    + Software Updates
    + Repository Management
    + Debug Reports (SoS Reports)

Browser Support
===============

Desktop Browser Support:
-----------------------
* **Internet Explorer:** Current version
* **Chrome:** Current version
* **Firefox:** Current version
* **Safari:** Current version
* **Opera:** Current version

Mobile Browser Support:
-----------------------
* **Safari iOS:** Current-1 version
* **Android Browser** Current-1 version

Hypervisor Distro Support
=========================

Ginger Base and Wok might run on any GNU/Linux distribution that meets the
conditions described on the 'Getting Started' section below.

The Ginger community makes an effort to test it with the latest versions of
Fedora, RHEL, OpenSuSe, and Ubuntu.

Getting Started
===============

All Ginger Base functionalities are provided to user by Wok infra-structure.
It's important to install Wok before any Ginger Base operation be enabled on
the system.

There are two ways to have Ginger Base and Wok running together: by their
packages (latest release) or by source code (development release).

Installing From Packages
------------------------

Kimchi and Ginger teams provide packages of the latest stable release of Wok
and Ginger Base. To install them, follow these instructions:

**For Fedora:**

```
$ wget http://kimchi-project.github.io/wok/downloads/wok-2.0.0-0.fc23.noarch.rpm
$ wget http://kimchi-project.github.io/gingerbase/downloads/ginger-base-2.0.0-0.fc23.noarch.rpm
$ sudo dnf install wok-*.rpm ginger-base-*.rpm
```

**For RHEL:**

```
$ wget http://kimchi-project.github.io/wok/downloads/wok-2.0.0-0.el7.noarch.rpm
$ wget http://kimchi-project.github.io/gingerbase/downloads/ginger-base-2.0.0-0.el7.noarch.rpm
$ sudo yum install wok-*.rpm ginger-base-*.rpm
```

**For Debian/Ubuntu:**

```
$ wget http://kimchi-project.github.io/wok/downloads/wok-2.0.0-0.noarch.deb
$ wget http://kimchi-project.github.io/gingerbase/downloads/ginger-base-2.0.0-0.noarch.deb
$ sudo dpkg -i wok-*.deb ginger-base-*.deb
```

**For openSUSE:**

```
$ wget http://kimchi-project.github.io/wok/downloads/wok-2.0.0-0.noarch.rpm
$ wget http://kimchi-project.github.io/gingerbase/downloads/ginger-base-2.0.0-0.noarch.rpm
$ sudo zypper install wok-*.rpm ginger-base-*.rpm
```

Installing from Source Code
---------------------------

Before anything, it's necessary install Wok and Ginger Base dependencies. To
install Wok dependencies, see Wok's README file at
https://github.com/kimchi-project/wok/blob/master/docs/README.md

To install Ginger Base dependencies, follow:

**For Fedora and RHEL:**

    $ sudo yum install rpm-python sos pyparted python-configobj

    # If using Fedora, install the following additional packages:
    $ sudo yum install python2-dnf

*Note for RHEL users*: Some of the above packages are located in the Red Hat
EPEL repositories.  See
[this FAQ](http://fedoraproject.org/wiki/EPEL#How_can_I_use_these_extra_packages.3F)
for more information on how to configure your system to access this repository.

And for RHEL7 systems, you also need to subscribe to the "RHEL Server Optional"
channel at RHN Classic or Red Hat Satellite.

**For Debian/Ubuntu:**

    $ sudo apt-get install python-apt sosreport python-configobj python-parted

**For openSUSE:**

    $ sudo zypper install rpm-python python-parted python-configobj

*Note for openSUSE users*: Some of the above packages are located in different
openSUSE repositories. See
[this FAQ](http://software.opensuse.org/download.html?project=home%3AGRNET%3Asynnefo&package=python-parted) for
python-parted package.

After install and resolve all dependencies, clone both source code:

```
$ git clone --recursive https://github.com/kimchi-project/wok.git
$ cd wok
$ git submodule update --remote
$ ./build-all.sh
```

To run Ginger Base tests, execute:

```
$ cd src/wok/plugins/gingerbase
$ make check-local                      # check for i18n and formatting errors
$ sudo make check                       # execute unit tests
```

After all tests are executed, a summary will be displayed containing any
errors/failures which might have occurred.

Regarding UI development, make sure to update the CSS files when modifying the
SCSS files by running:

    $ sudo make -C ui/css css


Run
---

    $ sudo systemctl start wokd.service


Usage
-----

Connect your browser to https://localhost:8001.
Once logged in you could see host tab which provides the gingerbase functionality.

Wok uses PAM to authenticate users so you can log in with the same username
and password that you would use to log in to the machine itself.

![Ginger Base Host Screen](docs/gingerbase-host-tab.png)

Ginger Base Host tab provides the base host functionality like system information,
 system statistics, software updates, repositories and debug reports functionality.

Also Ginger Base provides shutdown, re-start and connect options.

Participating
-------------

All patches are sent through our mailing list.  More information can be found at:

https://github.com/kimchi-project/ginger/wiki/Communications

Patches should be sent using git-send-email to ginger-dev-list@googlegroups.com
