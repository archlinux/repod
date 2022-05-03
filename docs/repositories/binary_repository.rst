.. _binary repository:

=================
Binary Repository
=================

A binary repository is a directory exposed by a web server, that contains built
package files of precompiled software, which can be installed using |pacman|.
Apart from the packages and their potential signature files, :ref:`sync
database` files are also present.

.. note::

  For performance reasons, a binary repository does not contain package files
  directly, as it would require moving files (e.g. from a staging repository to
  a testing repository). Instead, files are symlinked from a :ref:`package
  pool`, which renders moves between repositories a near-instant operation.

A binary repository usually targets a specific stability guarantee (e.g.
``staging``, ``testing`` or ``stable``) and depending on this should be
consistent among the packages it provides (e.g. a package in ``stable`` must
not depend on a |soname| only provided by a package in ``staging``).

The below example shows the directory layout of a binary repository named
``repo`` alongside its :ref:`package pool` directory with a single package in
it.

.. code::

  .
  ├── /srv/ftp/repo
  │   └── x86_64
  │       ├── package-1.0.0-1-x86_64.pkg.tar.zst -> ../../pool/package-1.0.0-1-x86_64.pkg.tar.zst
  │       ├── package-1.0.0-1-x86_64.pkg.tar.zst.sig -> ../../pool/package-1.0.0-1-x86_64.pkg.tar.zst.sig
  │       ├── repo.db
  │       └── repo.files
  └── /srv/ftp/pool
      ├── package-1.0.0-1-x86_64.pkg.tar.zst
      └── package-1.0.0-1-x86_64.pkg.tar.zst.sig

.. _package pool:

Package Pool
------------

A package pool is a directory, that contains package files and their potential
signatures. Symlinks in :ref:`binary repository` directories target files in a
package pool, so that files do not have to be moved (instead symlinks are
created and cleaned up).

.. |pacman| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/pacman.8.en">pacman</a>

.. |soname| raw:: html

  <a target="blank" href="https://en.wikipedia.org/wiki/Soname">soname</a>
