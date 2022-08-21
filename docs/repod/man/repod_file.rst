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

TRANSFORM REPOSITORY SYNC DATABASE TO MANAGEMENT REPOSITORY
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

To import :ref:`default sync database` files and output them to the management
repository directory of a configured repository, use:

.. code:: sh

  repod-file repo importdb /var/lib/pacman/sync/core.db default

To be able to use :ref:`files sync database` files, make sure to update them
first.

.. code:: sh

  pacman -Fy

Afterwards it is possible to import those files analogous to how it is done
with :ref:`default sync database` files:

.. code:: sh

  repod-file repo importdb /var/lib/pacman/sync/core.files default

The above assumes the repository named *default* is present (e.g. when no
configuration file for repod is present).

.. _management_repo_to_syncdb:

TRANSFORM MANAGEMENT REPOSITORY TO REPOSITORY SYNC DATABASE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The JSON files contained in a :ref:`management repository` can be transformed
into a :ref:`sync database` (both :ref:`default sync database` and :ref:`files
sync database` files are created).

After following the examples in :ref:`syncdb_to_management_repo`, it is
possible to use the created files and turn them back into :ref:`sync database`
files.

.. code:: sh

  repod-file repo writedb default

The above creates ``default.db`` as well as ``default.files`` in the binary
repository location of the repository named *default*.

.. |pacman| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/pacman.8">pacman</a>

SEE ALSO
--------

:manpage:`repod.conf(5)`, :manpage:`BUILDINFO(5)`, :manpage:`mtree(5)`, :manpage:`pacman(8)`
