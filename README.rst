arch-repo-management
####################

This is a PoC for a modular, Python based tool, that can manage git based
repositories (the details are explained below) and their respective binary
repository counterparts. The two not necessarily have to be located on the same
host.

The below implementational details need to be mocked and tested against each
other.

Git repository layout
_____________________

The package repositories (one git repository for each `pkgbase`_) are
managed by their maintainers::

  package_a
  package_b
  package_c

Following is an attempt to draw out a couple of potential designs for how to
keep track of which version of which package is currently in which (binary
package) repository.
Some share a common design: Keep track of all available `PKGBUILD`_ files
of all packages in a single (`architecture`_ specific, e.g. *x86_64*)
repository (grouped by repository)::

  x86_64
    core
      package_a
    core-debug
    extra
      package_b
    extra-debug
    staging
    testing
    community
      package_c
    community-debug
    community-staging
    community-testing
    gnome-unstable
    kde-unstable
    multilib
    multilib-debug
    multilib-staging
    multilib-testing

Others follow a more minimalistic approach, in which tracking of the package
repositories is only done indirectly. In these scenarios, *a)* per repository
plaintext files keep track of the packages and their respective current
versions, or *b)* per package plaintext files in repository directories keep
track of their respective versions.

a)::

  x86_64
    core.txt
    core-debug.txt
    extra.txt
    extra-debug.txt
    staging.txt
    testing.txt
    community.txt
    community-debug.txt
    community-staging.txt
    community-testing.txt
    gnome-unstable.txt
    kde-unstable.txt
    multilib.txt
    multilib-debug.txt
    multilib-staging.txt
    multilib-testing.txt

b)::

  x86_64
    core
      package_a.txt
    core-debug
    extra
      package_b.txt
    extra-debug
    staging
    testing
    community
    community-debug
    community-staging
    community-testing
    gnome-unstable
    kde-unstable
    multilib
    multilib-debug
    multilib-staging
    multilib-testing

Per-architecture monorepo using subtree
=======================================

The different packages are being tracked using `git-subtree`_.

**Pros**:

- low complexity operations with logging (e.g. `git-mv`_ to move packages from
  one repo to the other)
- `git-log`_ can carry all information of all packages
- can manage the subtrees the same as the main repository

**Cons**:

- more features than required
- potentially intransparent to use
- potentially very slow over time
- potentially convoluted `git-log`_ as it's harder to define messages
  specifically

Per-architecture monorepo using read-tree
=========================================

The different packages are merged in using `git-read-tree`_.

**Pros**:

- low complexity operations with logging (e.g. `git-mv`_ to move packages from
  one repo to the other)
- `git-log`_ messages can be defined more easily
- higher transparency of what gets merged

**Cons**:

- potentially very slow over time

Per-architecture monorepo using submodule
=========================================

The different packages are tracked using `git-submodule`_.

**Pros**:

- declarative syntax in `.gitmodules`_
- transparent locking/ pinning

**Cons**:

- moving becomes potentially more complex (deinit/init)
- updating becomes potentially more complex
- `git-log`_ only reflects to which commit a submodule was updated
- needs ``submodule init --update --recursive`` to be fully functional

Per-architecture repo with per-repo plaintext file
==================================================

The package names and versions are tracked in per-repository plaintext files
(e.g. `x86_64/core.txt`)::

  package_a 0.0.1
  package_b 0.2.1

**Pros**:

- very simple
- very fast
- only few files
- no additional git plumbing required
- package moving (between repositories) requires operations on two files

**Cons**:

- intransparent (package details can not be retrieved in one place)
- per package build scripts are held separately

Per-architecture repo with per-package plaintext file in repo directories
=========================================================================

The package versions are tracked in per-package plaintext files in repository
directory structures (e.g. `x86_64/core/package_a.txt`)::

  0.0.1

**Pros**:

- very simple
- very fast
- as many plaintext files as there are packages
- no additional git plumbing required
- package moving (between repositories) requires one file move operation

**Cons**:

- intransparent (package details can not be retrieved in one place)
- per package build scripts are held separately

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

  core
    os
      x86_64
        core.db
        [..]
        package_a-1:2-3-x86_64.pkg.tar.xz -> ../../../pool/package_a-1:2-3-x86_64.pkg.tar.xz
        package_a-1:2-3-x86_64.pkg.tar.xz.sig -> ../../../pool/package_a-1:2-3-x86_64.pkg.tar.xz.sig
        [..]
  pool
    [..]
    package_a-1:2-3-x86_64.pkg.tar.xz
    package_a-1:2-3-x86_64.pkg.tar.xz.sig
    [..]

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
#. Sign *package*
#. Upload built *package* and signature
#. Call application on repository/ package server to add *package*

**Repository server/ package server**:

.. important::
   The following steps need to be atomic (reversable).

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
   The following steps need to be atomic (reversable).

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
   The following steps need to be atomic (reversable).

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

Following are a set of proposed tests to derive the best possible
implementation from this.

Unit Tests
==========

All submitted code should have 100% unit test coverage and be documented.

Integration Tests
=================

The different repository layout approaches need to be mockable, by creating
fixtures from scratch in a test run (for reproducibility).
The tests should be able to cover use-case in which a couple of thousand
operations can be mocked in sequence to track and measure the eventual required
turnaround time of each approach.

.. _pkgbase: https://jlk.fjfi.cvut.cz/arch/manpages/man/core/pacman/PKGBUILD.5.en#PACKAGE_SPLITTING
.. _PKGBUILD: https://jlk.fjfi.cvut.cz/arch/manpages/man/core/pacman/PKGBUILD.5.en
.. _git-subtree: https://jlk.fjfi.cvut.cz/arch/manpages/man/extra/git/git-subtree.1.en
.. _git-read-tree: https://jlk.fjfi.cvut.cz/arch/manpages/man/extra/git/git-read-tree.1.en
.. _git-submodule: https://jlk.fjfi.cvut.cz/arch/manpages/man/extra/git/git-submodule.1.en
.. _.gitmodules: https://jlk.fjfi.cvut.cz/arch/manpages/man/extra/git/gitmodules.5.en
.. _git-mv: https://jlk.fjfi.cvut.cz/arch/manpages/man/extra/git/git-mv.1.en
.. _git-log: https://jlk.fjfi.cvut.cz/arch/manpages/man/extra/git/git-log.1.en
.. _architecture: https://jlk.fjfi.cvut.cz/arch/manpages/man/core/pacman/PKGBUILD.5.en#OPTIONS_AND_DIRECTIVES

