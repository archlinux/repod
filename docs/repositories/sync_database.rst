=============
Sync database
=============

Pacman downloads remote database files, that it uses to synchronize its local
state with a remote binary repository and to figure out which packages to
download and upgrade.

The sync database files are tar files, that may be gzip, bzip2, xz or zstd
compressed. Two types of files are supported: Default sync databases
(suffixed with ``.db``) and files databases (suffixed with ``.files``).

Default database
----------------

In the default database each package in its current version is represented by a
directory and a ``desc`` file::

  .
  ├── package-1.0.0-1
  │   └── desc
  [..]

A ``desc`` file carries identifiers and their values, which describe a package
(see :ref:`desc`).

Files database
--------------

In the files database each package in its current version is represented by a
directory containing a ``desc`` and a ``files`` file::

  .
  ├── package-1.0.0-1
  │   ├── desc
  │   └── files
  [..]

The ``desc`` file is the same as in the default database, while the ``files``
file represents the list of files of a given package (see :ref:`files`).
