.. _package contents:

================
Package Contents
================

A package contains files that are installed on a target system as well as
additionals, which are only relevant for the package manager and the repository
management software (e.g. to create entries in the :ref:`management repository`
and :ref:`sync database`).

.. _mtree:

.MTREE
------

The ``.MTREE`` files contained in a package are |mtree| files, which describe
the contents of a package. Entities such as directories, files and symlinks are
described in a binary format that lists their ownership, permissions, creation
date and various checksums.

Not all |mtree| keywords are used during package creation, which means that
only a subset of them are available in the eventual ``.MTREE`` file.

.. _mtree json schema:

MTreeEntry
^^^^^^^^^^

The entries of an ``.MTREE`` file are parsed and can subsequently be described
by a JSON schema.

Below is a list of currently understood versions of the schema.

.. _mtreeentryv1:

MTreeEntryV1
""""""""""""

.. literalinclude:: schema/MTreeEntryV1.json
   :language: json

.. |mtree| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/mtree.5">mtree</a>
