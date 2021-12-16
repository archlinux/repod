arch-repo-management
####################

This is a PoC for a modular, Python based tool, that can manage git based
repositories (the details are explained below) and their respective binary
repository counterparts. The two not necessarily have to be located on the same
host.

The below implementational details need to be mocked and tested against each
other.

Previous discussion: https://conf.archlinux.org/reports/archconf_2019/

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

.. _PKGBUILD: https://man.archlinux.org/man/pacman/PKGBUILD.5.en
.. _git-subtree: https://man.archlinux.org/man/git/git-subtree.1.en
.. _git-read-tree: https://man.archlinux.org/man/git/git-read-tree.1.en
.. _git-submodule: https://man.archlinux.org/man/git/git-submodule.1.en
.. _.gitmodules: https://man.archlinux.org/man/git/gitmodules.5.en
.. _git-mv: https://man.archlinux.org/man/git/git-mv.1.en
.. _git-log: https://man.archlinux.org/man/git/git-log.1.en
.. _architecture: https://man.archlinux.org/man/pacman/PKGBUILD.5.en#OPTIONS_AND_DIRECTIVES

