.. _tooling:

=======
Tooling
=======

The repod project provides scripts, that can be used to manipulate data, which
is related to the repositories it can manage.

.. _repod-file:

repod-file
----------

The ``repod-file`` script can be used to inspect and transform data related to
:ref:`package`, :ref:`sync database` and :ref:`management repository` files.

.. note::

   Refer to ``repod-file --help`` for further information on subcommands,
   options and parameters.

.. _inspect_package_files:

Inspecting Package files
^^^^^^^^^^^^^^^^^^^^^^^^

:ref:`package` files can be inspected to review the metadata contained in them.

To get the entire metadata collected by repod, use:

.. code:: sh

  repod-file package inspect <package>

.. note::

  By default package signature files are not considered. To enforce the
  locating and use of accompanying signature files, use the ``-s``/
  ``--with-signature`` flag.

The output of ``repod-file package inspect`` can be modified by using the
``-p``/ ``--pretty`` option (for pretty printing the JSON output).

To only display subsets of the data, refer to the following flags:

* ``-B``/ ``--buildinfo`` (for :ref:`buildinfo`)
* ``-M``/ ``--mtree`` (for :ref:`mtree`)
* ``-P``/ ``--pkginfo`` (for :ref:`pkginfo`).

.. _package_to_management_repo:

Import Package metadata to management repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The metadata retrieved from :ref:`package` files and their :ref:`package
signature` can be transformed to their respective :ref:`management repository`
representation. For this to produce meaningful and complete output, all
packages (and their signatures) of a given ``pkgbase`` (see |package
splitting|) need to be consumed at once.

.. code:: sh

  repod-file package import <package> <repo>

.. note::

  By default package signature files are not considered. To enforce the
  locating and use of accompanying signature files, use the ``-s``/
  ``--with-signature`` flag.

The output of the above command may be displayed using the ``-d``/
``--dry-run`` flag (nothing is written to the output directory in this case).
To pretty print the JSON output use the ``-p``/ ``--pretty`` flag.

.. _syncdb_to_management_repo:

Transform repository sync databases to management repository
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

Transform management repositories to repository sync databases
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The JSON files contained in a :ref:`management repository` can be transformed
into a :ref:`sync database` (both :ref:`default sync database` and :ref:`files
sync database` files are created).

After following the examples in :ref:`syncdb_to_management_repo` it is possible
to use the created files and turn them back into :ref:`sync database` files.

.. code:: sh

  SYNC_DB_OUTPUT="$(mktemp -d)"
  echo "$SYNC_DB_OUTPUT"
  repod-file management export "$FILES_JSON_OUTPUT" "$SYNC_DB_OUTPUT/core.db"

The above creates ``"$SYNC_DB_OUTPUT/core.db"`` as well as
``"$SYNC_DB_OUTPUT/core.files"``.

.. _json_schema_export:

Export JSON schema
^^^^^^^^^^^^^^^^^^

To export the |JSON schema|, which represents the validation logic of repod, use:

.. code:: sh

  REPOD_SCHEMA="$(mktemp -d)"
  echo "$REPOD_SCHEMA"
  repod-file schema export "$REPOD_SCHEMA"

.. |pacman| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/pacman.8">pacman</a>

.. |JSON schema| raw:: html

  <a target="blank" href="https://en.wikipedia.org/wiki/JSON#Metadata_and_schema">JSON schema</a>

.. |package splitting| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/PKGBUILD.5#PACKAGE_SPLITTING">package splitting</a>
