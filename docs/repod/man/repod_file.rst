.. _repod-file:

==========
repod-file
==========

.. argparse::
   :module: repod.cli.argparse
   :func: sphinx_repod_file
   :prog: repod-file

EXAMPLES
--------

.. _syncdb_to_management_repo:

TRANSFORM REPOSITORY SYNC DATABASES TO MANAGEMENT REPOSITORY
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:ref:`sync database` files can be transformed to representations used in the
context of a :ref:`management repository`.

.. note::

  :ref:`files sync database` files are required to create :ref:`management
  repository` files, that contain information on files contained in the
  respective packages they represent! This data is not contained in the
  :ref:`default sync database` files!

For testing purposes, the system's |pacman| sync databases in
``/var/lib/pacman/sync/`` can be used (this assumes a system that makes use of
pacman as package manager).

To transform :ref:`default sync database` files and output them to a temporary
directory, you can use the following:

.. code:: sh

  DEFAULT_JSON_OUTPUT="$(mktemp -d)"
  echo "$DEFAULT_JSON_OUTPUT"
  repod-file syncdb export /var/lib/pacman/sync/core.db "$DEFAULT_JSON_OUTPUT"

To be able to use :ref:`files sync database` files, make sure to update them
first.

.. code:: sh

  pacman -Fy

Afterwards you are able to transform the files and output them to a temporary
directory as well:

.. code:: sh

  FILES_JSON_OUTPUT="$(mktemp -d)"
  echo "$FILES_JSON_OUTPUT"
  repod-file syncdb export /var/lib/pacman/sync/core.files "$FILES_JSON_OUTPUT"

.. _management_repo_to_syncdb:

TRANSFORM MANAGEMENT REPOSITORIES TO REPOSITORY SYNC DATABASES
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The JSON files contained in a :ref:`management repository` can be transformed
into a :ref:`sync database` (both :ref:`default sync database` and :ref:`files
sync database` files are created).

After following the examples :ref:`above <syncdb_to_management_repo>`, it is
possible to use the created files and turn them back into :ref:`sync database`
files.

.. code:: sh

  SYNC_DB_OUTPUT="$(mktemp -d)"
  echo "$SYNC_DB_OUTPUT"
  repod-file management export "$FILES_JSON_OUTPUT" "$SYNC_DB_OUTPUT/core.db"

The above creates ``"$SYNC_DB_OUTPUT/core.db"`` as well as
``"$SYNC_DB_OUTPUT/core.files"``.

.. |pacman| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/pacman.8">pacman</a>

.. |JSON schema| raw:: html

  <a target="blank" href="https://en.wikipedia.org/wiki/JSON#Metadata_and_schema">JSON schema</a>

.. |package splitting| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/PKGBUILD.5#PACKAGE_SPLITTING">package splitting</a>

SEE ALSO
--------

:manpage:`repod.conf(5)`, :manpage:`BUILDINFO(5)`, :manpage:`mtree(5)`, :manpage:`pacman(8)`
