arch-repo-management
####################

This is a PoC for a modular, Python based tool, that can manage git based
repositories (the details are explained below) and their respective binary
repository counterparts. The two not necessarily have to be located on the same
host.

The below implementational details need to be mocked and tested against each
other.

Previous discussion: https://conf.archlinux.org/reports/archconf_2019/

Git repository layout
_____________________

The package repositories (one git repository for each `pkgbase`_) are
managed by their maintainers::

  pkgbase_a
  pkgbase_b
  pkgbase_c

Tracking of the package repositories is done through package metadata
files in repository directories. These files contain the metadata
available in pacman(8) packages, and may be generated directly from
them::

  .
  └── meta
      └── x86_64
          ├── core
          │   └── pkgbase_a.json
          ├── core-debug
          └── extra
              └── pkgbase_b.json
          ├── extra-debug
          ├── staging
          ├── testing
          ├── community
          ├── community-debug
          ├── community-staging
          ├── community-testing
          ├── gnome-unstable
          ├── kde-unstable
          ├── multilib
          ├── multilib-debug
          ├── multilib-staging
          └── multilib-testing

.. note::
   Unlike svn, there is no distinction between repositories, in
   particular between `community` and packages in other repositories
   such as `extra`.

Per-architecture repo with per-package metadata file in repo directories
=========================================================================

The package versions are tracked in per-package metadata files in repository
directory structures (e.g. `x86_64/core/nmon.json`)::

  {
    "packages": [
        {
            "arch": "x86_64",
            "builddate": 1569502151,
            "csize": 66224,
            "depends": [
                "ncurses"
            ],
            "desc": "AIX & Linux Performance Monitoring tool",
            "filename": "nmon-16m-1-x86_64.pkg.tar.xz",
            "files": [
                "usr/",
                "usr/bin/",
                "usr/bin/nmon"
            ],
            "isize": 184320,
            "licenses": [
                "GPL"
            ],
            "md5sum": "e19d219d24863eb67a301fdaec765ca4",
            "name": "nmon",
            "packager": "Massimiliano Torromeo <massimiliano.torromeo@gmail.com>",
            "pgpsig": "iF0EABECAB0WIQQsEYxiDwLbmsHQ+fqU3SOT2i7kIwUCXYyz2QAKCRCU3SOT2i7kI8//AJ9578YSlZVWkdo41a9sjqgw1cOYOgCfcAYFaI19lgcC9Tws3jynEufvayA=",
            "sha256sum": "b4757bfc682f3a1f178675be2c05f8c32047b3cf32da05fa97a2a4101696359f",
            "url": "http://nmon.sourceforge.net"
        }
    ],
    "version": "16m-1"
  }

File format with sorted keys JSON and fields::

    version
    makedepends (list)
    checkdepends (list)
    packages (list of objects with fields below)
    filename
    name
    desc
    groups (list)
    csize (int)
    isize (int)
    md5sum
    sha256sum
    pgpsig
    url
    license (list)
    arch (because can also be "any")
    builddate (int)
    packager
    replaces (list)
    conflicts (list)
    provides (list)
    depends (list)
    optdepends (list)
    backup (list)
    files (list)

.. note::
   If a key is not defined in a package (e.g. `checkdepends`) it is
   not added to the metadata file.

**Pros**:

- very simple
- very fast
- no additional git plumbing required
- as many JSON files as there are packages

  - all metadata (including file paths) can be included with reasonable file size

- package moving (between repositories) requires one file move operation
- generate DB files directly from repo state

  - keep history of precise state of Arch Linux repositories at any given time

**Cons**:

- per package build scripts are held separately
- possible mismatches between repo-add and dbscripts-generated databases

  - continuous integration/testing

.. note::
   JSON is chosen for ease-of-use with Python.

Binary repository layout
________________________

The git repository layout directly reflects the binary repository layout. This
means, that the location of a *package*'s git repository in its specific
location needs to match its built package in the respective binary repository
(which is implemented by a symlink from a *pool* directory)

If *package_a* in version *1:2-3* is in::

  x86_64
    core
      package_a

its binary package will be symlinked from the pool to the respective location::

  .
  ├── /srv/ftp/core
  │   └── os
  │       └── x86_64
  │           ├── core.db
  │           ├── [..]
  │           ├── package_a-1:2-3-x86_64.pkg.tar.xz -> ../../../pool/package_a-1:2-3-x86_64.pkg.tar.xz
  │           ├── package_a-1:2-3-x86_64.pkg.tar.xz.sig -> ../../../pool/package_a-1:2-3-x86_64.pkg.tar.xz.sig
  │           └── [..]
  └── /srv/ftp/pool
      ├── [..]
      ├── package_a-1:2-3-x86_64.pkg.tar.xz
      ├── package_a-1:2-3-x86_64.pkg.tar.xz.sig
      └── [..]

Workflows
_________

In this section the different workflows are listed, to give an overview, what
they would mean in the different git repository layouts.

Adding a Package
================

**Developer machine/ build server**:

#. Create repository
#. Update, build *package* and commit changes in *package*'s `PKGBUILD`_
#. Tag release
   .. note::
   Force pushing tags is disallowed.
#. Sign *package*
#. Upload built *package* and signature
#. Call application on repository/ package server to add *package*

**Repository server/ package server**:

.. important::
   The following steps need to be atomic (reversible).

#. Verify user permissions
#. Lock package database and monorepo
#. Inspect built files of *package*
#. Lock tags (by storing them in *package*'s bare repository)
#. **Modify monorepo to reflect changes**
#. Verify *package* file versioning and tag is consistent
#. Copy built *package* and signature to pool and create symlink to them in
   target repository
#. Add *package* to the package database
#. Unlock package database and monorepo

Updating a Package
==================

All steps, but the first, of **Developer machine/ build server** in `Adding a
Package`_ apply.

All steps of **Repository server/ package server** in `Adding a Package`_ apply.

Removing a Package
==================

**Developer machine/ build server**:

#. Call application on repository/ package server to remove *package*

**Repository server/ package server**:

.. important::
   The following steps need to be atomic (reversible).

.. note::
   The remove command should be able to remove stale packages (e.g. leftover
   packages, when removing a member of a split package)

#. Verify user permissions
#. Lock package database and monorepo
#. **Modify monorepo to reflect changes**
#. Remove *package* from the package database
#. Remove built *package* and signature from pool and remove symlink to them in
   target repository
#. Unlock package database and monorepo

Moving a Package
================

**Developer machine/ build server**:

#. Call application on repository/ package server to move *package*

**Repository server/ package server**:

.. important::
   The following steps need to be atomic (reversible).

#. Verify user permissions
#. Lock source and target package databases and monorepo
#. **Modify monorepo to reflect changes**
#. Remove *package* from the source package database
#. Add *package* to the destination package database
#. Remove symlinks to package and signature files from source repository and
   add them to the target repository
#. Unlock source and target package databases and monorepo

TODO
____

dbscripts
=========

Add/Update
----------

Integrate new .pkg.tar.xz for one or multiple pkgbases into the DB.

- **DONE** Collect packages from staging dir, parse .PKGINFO

  - **DONE** Group by repo and pkgbase

    - **DONE** `{'extra': {'foo': data, 'bar': data}, 'testing': { ... }}`
    - **DONE** if pkgbase already seen but common fields (version, makedepends, checkdepends) differ, error out
    - **DONE** do GPG verification?

- **DONE** For each repo to process:

  - **DONE** Load repo JSON data

- For each pkgbase:

  - **DONE** Ensure version is increasing (pyalpm vercmp)
  - Shallow clone tag named "$version" from package repository named "$pkgbase" to get PKGBUILD
  - GPG-verify tag?
  - Run `makepkg --packagelist` to get list of expected packages

    - Verify against packages collected

  - Do other verification checks between `PKGBUILD` and packages? Check current dbscripts
  - Get rid of clone
  - Copy the packages into the FTP pool

    - Existing file is an error

  - Link the packages from the FTP repo dir

    - Existing file is an error

  - Copy package data into repo data

- **DONE** Write out JSON
- **DONE** Write out DB files
- git commit
- Remove old symlinks

Remove
------

Remove existing pkgbases.

- **DONE** For each repo to process: (existing db-remove operates on a single repo)

  - **DONE** Load repo JSON data

- **DONE** For each pkgbase:

  - **DONE** Remove pkgbase from data

- **DONE** Delete JSON files
- **DONE** Write out DB files
- `git commit`
- **DONE** Remove old symlinks

Move
----
Move packages from one repository (e.g. testing) to another (e.g. extra).

- **DONE** For each repo to process:

  - **DONE** Load repo JSON data

- For each pkgbase:

  - **DONE** Move data
  - Add new symlinks

- **DONE** Write out JSON
- **DONE** Write out DB files
- `git commit`
- Remove old symlinks

Tasks
-----

- Code to load JSON and stream out a database - heftig

  - Generates a tar written to the `foo.db.tar.gz`

- Code to load packages and write out JSON - maximbaz
- **DONE** For testing purposes, code to convert a `foo.db.tar.gz` into JSON - alad
- Rewrite devtools' commitpkg to use git instead of svn

.. _pkgbase: https://man.archlinux.org/man/pacman/PKGBUILD.5.en#PACKAGE_SPLITTING
.. _PKGBUILD: https://man.archlinux.org/man/pacman/PKGBUILD.5.en
.. _git-subtree: https://man.archlinux.org/man/git/git-subtree.1.en
.. _git-read-tree: https://man.archlinux.org/man/git/git-read-tree.1.en
.. _git-submodule: https://man.archlinux.org/man/git/git-submodule.1.en
.. _.gitmodules: https://man.archlinux.org/man/git/gitmodules.5.en
.. _git-mv: https://man.archlinux.org/man/git/git-mv.1.en
.. _git-log: https://man.archlinux.org/man/git/git-log.1.en
.. _architecture: https://man.archlinux.org/man/pacman/PKGBUILD.5.en#OPTIONS_AND_DIRECTIVES

