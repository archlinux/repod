.. _source tarball repository:

=========================
Source Tarball Repository
=========================

A source tarball repository is a directory exposed by a web server, that
contains source tarballs of packages in a :ref:`binary repository`.
The tarballs are created from |PKGBUILD| files found in a :ref:`source
repository`.

.. note::

  For performance reasons, a source tarball repository does not contain tarball
  files directly, as it would require moving files (e.g. from one repository to
  another). Instead, files are symlinked from a :ref:`source tarball pool`,
  which renders moves between repositories a near-instant operation.

.. _source tarball pool:

Source Tarball Pool
-------------------

A source tarball pool is a directory, that contains tarball files. Symlinks in
:ref:`source tarball repository` directories target files in a source tarball
pool, so that files do not have to be moved (instead symlinks are created and
cleaned up).

.. |PKGBUILD| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/PKGBUILD.5">PKGBUILD</a>
