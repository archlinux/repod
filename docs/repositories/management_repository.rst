.. _management repository:

=====================
Management Repository
=====================

A management repository is a |version control repository|, that contains
machine readable descriptor files (i.e. |JSON|) which track the state of
:ref:`sync database` files and thus also of the :ref:`binary repository` they
describe.

Packages are gathered by ``pkgbase`` (see |PKGBUILD|) and the directory
structure follows a layout of **<CPU
architecture>**/**<repository>**/**<pkgbase>**, as the same repositories may
exist for several architectures.

.. code::

  .
  └── x86_64
      ├── core
      │   └── pkgbase_a.json
      ├── core-debug
      └── extra
          └── pkgbase_b.json
      ├── extra-debug
      ├── staging
      ├── testing
      ├── community
      ├── community-debug
      ├── community-staging
      ├── community-testing
      ├── gnome-unstable
      ├── kde-unstable
      ├── multilib
      ├── multilib-debug
      ├── multilib-staging
      └── multilib-testing

.. _json_schema:

JSON Schema
-----------

The |JSON| files contained in a :ref:`management repository` can be validated
using |JSON schema|.

The schema is derived from |pydantic| models, that allow to describe various
input files related to a :ref:`sync database`.

.. _files_schema:

Files
^^^^^

This is the schema of files that belongs to an :ref:`outputpackage_schema`.

Below is a list of currently understood versions of the schema.

.. _filesv1_schema:

FilesV1
"""""""

.. note::

   This schema represents the definition of :ref:`files_v1`.

.. literalinclude:: schema/FilesV1.json
   :language: json

.. _outputpackagebase_schema:

OutputPackageBase
^^^^^^^^^^^^^^^^^

This is the schema for a ``pkgbase`` file in the :ref:`management repository`.

.. note::

  In a |split package| scenario, the sum of information gathered from all
  packages, that belong to a given ``pkgbase`` comprise an
  :ref:`outputpackagebase_schema`.

Below is a list of currently understood versions of the schema.

.. _outputpackagebasev1_schema:

OutputPackageBaseV1
"""""""""""""""""""

.. literalinclude:: schema/OutputPackageBaseV1.json
   :language: json

.. _outputpackage_schema:

OutputPackage
^^^^^^^^^^^^^

This is the schema of a package that belongs to an
:ref:`outputpackagebase_schema`. It describes all properties that are unique to
the specific package and that are not also covered by the ``pkgbase``.

Below is a list of currently understood versions of the schema.

.. _outputpackagev1_schema:

OutputPackageV1
"""""""""""""""

.. literalinclude:: schema/OutputPackageV1.json
   :language: json

.. _packagedesc_schema:

PackageDesc
^^^^^^^^^^^

This is the schema of package information found in a :ref:`desc` file of a
:ref:`sync database`.

Below is a list of currently understood versions of the schema.

.. _packagedescv1_schema:

PackageDescV1
"""""""""""""

.. note::

   This schema represents the definition of :ref:`desc_v1`.

.. literalinclude:: schema/PackageDescV1.json
   :language: json

.. |version control repository| raw:: html

  <a target="blank" href="https://en.wikipedia.org/wiki/Repository_(version_control)">version control repository</a>

.. |PKGBUILD| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/PKGBUILD.5">PKGBUILD</a>

.. |JSON| raw:: html

  <a target="blank" href="https://en.wikipedia.org/wiki/JSON">JSON</a>

.. |JSON schema| raw:: html

  <a target="blank" href="https://en.wikipedia.org/wiki/JSON#Metadata_and_schema">JSON schema</a>

.. |pydantic| raw:: html

  <a target="blank" href="https://pydantic-docs.helpmanual.io/">pydantic</a>

.. |split package| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/PKGBUILD.5#PACKAGE_SPLITTING">split package</a>
