Management Repository
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

.. _pkgbase: https://man.archlinux.org/man/pacman/PKGBUILD.5.en#PACKAGE_SPLITTING
