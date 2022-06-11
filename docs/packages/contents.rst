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

.. _buildinfo:

.BUILDINFO
----------

The ``.BUILDINFO`` files contained in packages are |BUILDINFO| files, which
describe aspects of the build environment present during the creation of a
package.

Formats for the file are specified by |makepkg|. Its |write_buildinfo()|
function implements only the latest version of the available formats.

.. _buildinfo json schema:

BuildInfo
^^^^^^^^^

The entries in a ``.BUILDINFO`` file are parsed and can subsequently be
described by a JSON schema.

Below is a list of currently understood versions of the schema.

.. _buildinfov1:

BuildInfoV1
"""""""""""

.. literalinclude:: schema/BuildInfoV1.json
   :language: json

.. _buildinfov2:

BuildInfoV2
"""""""""""

.. note::

  If |devtools| has been used as ``buildtool``, the ``buildtoolver`` has to be
  of the form ``<optional_epoch><pkgver>-<pkgrel>-<arch>`` (e.g.
  ``20220207-1-any``)!

.. literalinclude:: schema/BuildInfoV2.json
   :language: json

.. _pkginfo:

.PKGINFO
--------

The ``.PKGINFO`` files contained in packages describe their metadata.

Formats for the file are specified by |makepkg|. Its |write_pkginfo()|
function implements only the latest version of the available formats.

.. _pkginfo json schema:

PkgInfo
^^^^^^^

The entries in a ``.PKGINFO`` file are parsed and can subsequently be described
by a JSON schema.

Below is a list of currently understood versions of the schema.

.. _pkginfov1:

PkgInfoV1
"""""""""

.. literalinclude:: schema/PkgInfoV1.json
   :language: json

.. _pkginfov2:

PkgInfoV2
"""""""""

In this version the ``pkgtype`` field has been added.

.. literalinclude:: schema/PkgInfoV2.json
   :language: json

.. |mtree| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/mtree.5">mtree</a>

.. |BUILDINFO| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/BUILDINFO.5">BUILDINFO</a>

.. |makepkg| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/makepkg.8">makepkg</a>

.. |write_buildinfo()| raw:: html

  <a target="blank" href="https://gitlab.archlinux.org/pacman/pacman/-/blob/bddfcc3f40ce1a19d4c9552cddbf2cab07c94d4b/scripts/makepkg.sh.in#L519-550">write_buildinfo()</a>

.. |write_pkginfo()| raw:: html

  <a target="blank" href="https://gitlab.archlinux.org/pacman/pacman/-/blob/bddfcc3f40ce1a19d4c9552cddbf2cab07c94d4b/scripts/makepkg.sh.in#L479-517">write_pkginfo()</a>

.. |devtools| raw:: html

  <a target="blank" href="https://gitlab.archlinux.org/archlinux/devtools">devtools</a>
