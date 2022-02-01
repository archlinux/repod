====================
arch-repo-management
====================

Arch-repo-management is a service to manage `pacman`_ based binary package
repositories.

.. note::
   At this point arch-repo-management is a work in progress and not yet
   feature complete. For an overview on what are the current features, see the
   Features section

As such this project deals with the creation and modification of **binary
repository databases** (usually maintained with the help of `repo-add`_ and
`repo-remove`_) and the handling of **binary package files** (usually created
using `PKGBUILD`_ and `makepkg`_) and their signatures in the context of
repositories.

The state of binary repository databases is described as a list of JSON files
(each describing a ``pkgbase`` - one or several binary packages) in a directory
structure which is tracked in a unified git repository - the **management
repository**. The binary repository database files and the management
repository can be translated back and forth from one another.

Binary package files are kept in **package pool directories**, from where they
are symlinked to **repository directories**.

Additions to a binary package repository are implemented as

- addition of a binary package file and its signature to a package pool directory
- a JSON file (derived from the binary package file) added to the management repository
- the binary package file and its signature symlinked into a repository directory
- the update of the binary repository database from the management repository state

Removals from a binary package repository are implemented as

- a JSON file (derived from the binary package file) removed from the management repository
- the update of the binary repository database from the management repository state
- removal of binary package file and signature symlink from the repository directory
- removal of the binary package file and its signature from a package pool directory

Movement of binary packages between binary package repositories is implemented as

- a JSON file (derived from the binary package file) moved within the management repository
- removal of binary package file and signature symlink from the old repository directory
- the binary package file and its signature symlinked into a new repository directory
- the update of the binary repository database from the management repository state

Features
========

The below features are defined in the scope of this project.

- [x] Create validated JSON descriptors for packages in a binary repository database
- [x] Create validated binary repository database from JSON descriptors
- [x] Self-validating configuration

  - [x] Describe staging and testing repositories for each stable repository
  - [x] Allow global default and per repository override of settings

- [ ] Documented example of configuration file `#27 <https://gitlab.archlinux.org/archlinux/arch-repo-management/-/issues/27>`_
- [ ] Handle state of binary repository database in the context of a VCS management repository `#12 <https://gitlab.archlinux.org/archlinux/arch-repo-management/-/issues/12>`_
- [ ] Handle stable locations of binary package files depending on (remote) package source location `#25 <https://gitlab.archlinux.org/archlinux/arch-repo-management/-/issues/25>`_
- [ ] Access Control List for packagers `#26 <https://gitlab.archlinux.org/archlinux/arch-repo-management/-/issues/26>`_
- [ ] Package actions in binary repository/pool as atomic and revertable action `#14 <https://gitlab.archlinux.org/archlinux/arch-repo-management/-/issues/14>`_
- [ ] Verify binary package file signature against predefined PGP keyring `#28 <https://gitlab.archlinux.org/archlinux/arch-repo-management/-/issues/28>`_
- [ ] Package group actions in binary repositories as atomic and revertable action `#30 <https://gitlab.archlinux.org/archlinux/arch-repo-management/-/issues/30>`_
- [ ] API for accepting package files and signatures `#31 <https://gitlab.archlinux.org/archlinux/arch-repo-management/-/issues/31>`_
- [ ] Systemd service running a service `#33 <https://gitlab.archlinux.org/archlinux/arch-repo-management/-/issues/33>`_
- [ ] Create client application for packagers `#34 <https://gitlab.archlinux.org/archlinux/arch-repo-management/-/issues/34>`_
- [ ] Sign binary repository database (locally and/ or with the help of a remote signing service) `#32 <https://gitlab.archlinux.org/archlinux/arch-repo-management/-/issues/32>`_

Installation
============

This project is Python based and uses `poetry`_.
To create sdist tarball and wheel::

  poetry build

To install the resulting wheel using pip::

  pip install dist/*.whl

Running
=======

At his point arch-repo-management exposes a set of scripts:

- ``db2json``: Translate a **binary repository database** into its **management repository** representation
- ``json2db``: Translate a directory within a **management repository** into its **binary repository database** representation

Contribute
==========

Development of arch-repo-management takes place on Arch Linux's Gitlab: https://gitlab.archlinux.org/archlinux/arch-repo-management.

Please read our distribution-wide `Code of Conduct <https://wiki.archlinux.org/title/Code_of_conduct>`_ before
contributing, to understand what actions will and will not be tolerated.

Read our `contributing guide <CONTRIBUTING.rst>`_ to learn more about how to provide fixes or improvements for the code
base.

Discussion around arch-repo-management takes place on the `arch-projects mailing list
<https://lists.archlinux.org/listinfo/arch-projects>`_ and in `#archlinux-projects
<ircs://irc.libera.chat/archlinux-projects>`_ on `Libera Chat <https://libera.chat/>`_.

All past and present authors of archiso are listed in `AUTHORS <AUTHORS.rst>`_.

License
=======

Arch-repo-management is licensed under the terms of the **GPL-3.0-or-later** (see `LICENSE <LICENSE>`_).

.. _pacman: https://gitlab.archlinux.org/pacman/pacman
.. _repo-add: https://man.archlinux.org/man/repo-add.8
.. _repo-remove: https://man.archlinux.org/man/repo-remove.8
.. _PKGBUILD: https://man.archlinux.org/man/PKGBUILD.5
.. _makepkg: https://man.archlinux.org/man/makepkg.8
.. _poetry: https://python-poetry.org/
