.. _tooling:

=======
Tooling
=======

The repod project provides scripts, that can be used to manipulate data, which
is related to the repositories it can manage.

.. _db2json:

db2json
-------

The ``db2json`` script can be used to transform a :ref:`sync database` (both
:ref:`default sync database` and :ref:`files sync database` files are
supported) into the JSON files found in a :ref:`management repository`.

.. note::

   Refer to ``db2json --help`` for further information on options and
   parameters.

For testing purposes, the system's |pacman| sync databases in
``/var/lib/pacman/sync/`` can be used.

To transform :ref:`default sync database` files in a temporary directory, you
can use the following:

.. code:: sh

  DEFAULT_JSON_OUTPUT="$(mktemp -d)"
  echo "$DEFAULT_JSON_OUTPUT"
  db2json /var/lib/pacman/sync/core.db "$DEFAULT_JSON_OUTPUT"

To be able to use :ref:`files sync database` files, make sure to update them
first.

.. code:: sh

  pacman -Fy

Afterwards you are able to transform the files in a temporary directory as
well:

.. code:: sh

  FILES_JSON_OUTPUT="$(mktemp -d)"
  echo "$FILES_JSON_OUTPUT"
  db2json /var/lib/pacman/sync/core.files "$FILES_JSON_OUTPUT"

.. _json2db:

json2db
-------

The ``json2db`` script can be used to transform the JSON files found in a
:ref:`management repository` into a :ref:`sync database` (both :ref:`default
sync database` and :ref:`files sync database` files are supported).

.. note::

   Refer to ``json2db --help`` for further information on options and
   parameters.

After following the examples in :ref:`db2json` it is possible to use the
created files and turn them back into :ref:`sync database` files.

.. code:: sh

   DEFAULT_DB_OUTPUT="$(mktemp -d)"
   echo "$DEFAULT_DB_OUTPUT"
   json2db "$DEFAULT_JSON_OUTPUT" "$DEFAULT_DB_OUTPUT/core.db"

Analogous to the above the example for the :ref:`files sync database` looks
very similar.

.. code:: sh

   FILES_DB_OUTPUT="$(mktemp -d)"
   echo "$FILES_DB_OUTPUT"
   json2db -f "$FILES_JSON_OUTPUT" "$FILES_DB_OUTPUT/core.files"

.. |pacman| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/pacman.8">pacman</a>
