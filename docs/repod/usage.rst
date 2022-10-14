.. _usage:

=====
Usage
=====

Repod offers the command-line interface (CLI) tool ``repod-file`` (for further
information refer to its manual: :ref:`repod-file`) to interact with package
files and repositories.

.. note::

  The ``repod-file`` tool is currently still limited in scope. It can

  * import packages to existing repositories
  * write repository sync databases
  * inspect package files
  * write JSON schema used by repod

The tool can be used per-user (reading configuration from
``$XDG_CONFIG_DIR/repod/repod.conf`` and
``$XDG_CONFIG_DIR/repod/repod.conf.d/`` and storing data below
``$XDG_STATE_DIR/repod/``) or system-wide (reading configuration from
``/etc/repod.conf`` and ``/etc/repod.conf.d/`` and storing data below
``/var/lib/repod/``).

By default ``repod-file`` can be used without a configuration file, as it will
assume a set of defaults (e.g. repository location, default repository name,
default repository architecture). However, it is advisable to create a
configuration file (see :ref:`repod.conf`), as it offers full control over
everything that repod has to offer.

.. note::

  In the future repod will be extended by a web service, which exposes an API
  (see `milestone 0.8.0
  <https://gitlab.archlinux.org/archlinux/repod/-/milestones/9>`_). This will
  likely change how interaction with the data maintained by repod takes place.

Using ``repod-file`` without a configuration file automatically creates a
repository with the name *default* and the CPU architecture *any*.

.. _importing packages:

Importing packages
==================

Packages can be imported to the default repository using

.. code:: bash

  repod-file repo importpkg package_a-1.0.0-1-any.pkg.tar.zst default


Assuming that the ``pkgbase`` (see `package splitting
<https://man.archlinux.org/man/PKGBUILD.5#PACKAGE_SPLITTING>`_) of
*package_a-1.0.0-1-any.pkg.tar.zst* is ``package_a``, the above command will
import the package to the repository named *default*, write the :ref:`sync
database` files for it and create the following directory structure:

.. code::

  /home/user/.local/state/repod
  ├── data
  │   ├── pool
  │   │   ├── package
  │   │   │   └── default
  │   │   │       └── package_a-1.0.0-1-any.pkg.tar.zst
  │   │   └── source
  │   │       └── default
  │   └── repo
  │       ├── package
  │       │   └── default
  │       │       └── any
  │       │           ├── default.db -> default.db.tar.gz
  │       │           ├── default.db.tar.gz
  │       │           ├── default.files -> default.files.tar.gz
  │       │           ├── default.files.tar.gz
  │       │           └── package_a-1.0.0-1-any.pkg.tar.zst -> ../../../../pool/package/default/package_a-1.0.0-1-any.pkg.tar.zst
  │       └── source
  │           └── default
  │               └── any
  └── management
      └── default
          └── any
              └── default
                  └── package_a.json

.. note::

  The data directory (e.g. ``$XDG_STATE_DIR/repod/data/``) is intended to be
  exposed by a webserver, as it represents the :ref:`binary repository`. The
  management directory (e.g. ``$XDG_STATE_DIR/repod/management/`` on the other
  hand is not supposed to be exposed publicly, as it represents the
  :ref:`management repository` and will gain the ability to expose itself using
  a git backend in the future (see `milestone 0.4.0
  <https://gitlab.archlinux.org/archlinux/repod/-/milestones/3>`_).

.. _writing sync databases:

Writing sync databases
======================

The writing of :ref:`sync database` files (as is done when :ref:`importing
packages`), can also be triggered manually.

.. code:: bash

  repod-file repo writedb default

The above command creates the following directory structure (assuming no
packages are present):

.. code::

  /home/user/.local/state/repod
  ├── data
  │   ├── pool
  │   │   ├── package
  │   │   │   └── default
  │   │   └── source
  │   │       └── default
  │   └── repo
  │       ├── package
  │       │   └── default
  │       │       └── any
  │       │           ├── default.db -> default.db.tar.gz
  │       │           ├── default.db.tar.gz
  │       │           ├── default.files -> default.files.tar.gz
  │       │           └── default.files.tar.gz
  │       └── source
  │           └── default
  │               └── any
  └── management
      └── default
          └── any
              └── default

.. _using repositories:

Using repositories
==================

Users of the pacman package manager can add a repository maintained by repod to
their pacman.conf (see `repository sections
<https://man.archlinux.org/man/pacman.conf.5#REPOSITORY_SECTIONS>`_ for
details).

We will assume, that repod's data directory is exposed at
*https://domain.tld*. The following addition to ``/etc/pacman.conf`` would then
allow users to install ``package_a`` from the *default* repository:

.. code:: ini

  [default]
  Server = https://domain.tld/repo/package/$repo/$arch
