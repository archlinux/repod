Packager Workflows
__________________

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
