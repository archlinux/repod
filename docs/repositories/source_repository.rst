.. _source repository:

=================
Source Repository
=================

A source repository is a |version control repository|, that contains the
necessary files to build a package. At the bare minimum this includes a
|PKGBUILD| and a ``.SRCINFO`` file, but may also contain an install script as
well as patches or other arbitrary files.

Using |makepkg|, the sources are used to build a package, which can be
installed with |pacman|. With the help of |package splitting| it is possible to
create more than one package from a single |PKGBUILD|.

.. note::

  Due to |dbscripts| and |makepkg| limitations it is currently not possible to
  target more than one :ref:`binary repository` with a single |PKGBUILD|.

.. _srcinfo:

.SRCINFO
--------

The ``.SRCINFO`` files contained in a :ref:`source repository` are data
representations of the accompanying |PKGBUILD| files and as such describe the
sources of any :ref:`package` build from it.

The files are read and parsed and can be described by the :ref:`srcinfov1` JSON
schema.

.. _pkgbase section:

Pkgbase section
^^^^^^^^^^^^^^^

This section of a ``.SRCINFO`` file describes the data common to all packages in
the |PKGBUILD| (this is similar to how :ref:`outputpackagebase_schema`
describes the data common to a set of packages in a :ref:`management
repository`).

The section is read and parsed when reading :ref:`srcinfo` files and must
exist. It can be described by the :ref:`pkgbasesectionv1` JSON schema.

.. _pkgname section:

Pkgname section
^^^^^^^^^^^^^^^

This section of a ``.SRCINFO`` file describes the data of a single package in
the |PKGBUILD|, which is different from the common data described by the
:ref:`pkgbase section` (this is similar to how :ref:`outputpackage_schema`
describes the data of a single package in a :ref:`management repository`).

The section may occur multiple times, but must exist at least once. It is read
and parsed when reading :ref:`srcinfo` files and can be described by the
:ref:`pkgnamesectionv1` JSON schema.

.. _srcinfo json schema:

JSON schema
^^^^^^^^^^^

.. _srcinfov1:

SrcInfoV1
"""""""""

.. literalinclude:: ../schema/SrcInfoV1.json
   :language: json

.. _pkgbasesectionv1:

PkgBaseSectionV1
""""""""""""""""

.. literalinclude:: ../schema/PkgBaseSectionV1.json
   :language: json

.. _pkgnamesectionv1:

PkgNameSectionV1
""""""""""""""""

.. literalinclude:: ../schema/PkgNameSectionV1.json
   :language: json


.. |version control repository| raw:: html

  <a target="blank" href="https://en.wikipedia.org/wiki/Repository_(version_control)">version control repository</a>

.. |PKGBUILD| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/PKGBUILD.5">PKGBUILD</a>

.. |makepkg| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/makepkg.8.en">makepkg</a>

.. |pacman| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/pacman.8.en">pacman</a>

.. |package splitting| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/PKGBUILD.5#PACKAGE_SPLITTING">package splitting</a>

.. |dbscripts| raw:: html

  <a target="blank" href="https://gitlab.archlinux.org/archlinux/dbscripts">dbscripts</a>
