.. _repod.conf:

==========
repod.conf
==========

.. _repod.conf_synopsis:

SYNOPSIS
--------

*$XDG_CONFIG_HOME/repod/repod.conf*

*$XDG_CONFIG_HOME/repod/repod.conf.d/*

*/etc/repod.conf*

*/etc/repod.conf.d/*

.. _repod.conf_description:

DESCRIPTION
-----------

A TOML based configuration file, which can be provided in a default
configuration file location and/ or override configuration file locations.
Override configuration files are read and merged in alphabetically order and
have higher precedence than the default configuration file location.

Configuration files provided in the system-wide locations (i.e.
``/etc/repod.conf`` and ``/etc/repod.conf.d/``) are only used for system-wide
use of repod, while configurations provided in per-user locations (i.e.
``$XDG_CONFIG_HOME/repod/repod.conf`` and
``$XDG_CONFIG_HOME/repod/repod.conf.d/``) are only used for per-user use of
repod.

If no configuration file is provided, defaults are assumed (see
:ref:`repod.conf_defaults`).

.. _repod.conf_global_options:

GLOBAL OPTIONS
--------------

Global options provide the defaults for any repository that does not define
them. For any undefined option defaults are assumed (see
:ref:`repod.conf_default_options`).

* *architecture*: A string setting the CPU architecture used for any
  repository, which does not define it.
  Understood values are

  .. program-output:: python -c "from repod.common.enums import ArchitectureEnum; print('\"' + '\", \"'.join([arch.value for arch in ArchitectureEnum]) + '\"')"

* *database_compression*: A string setting the database compression used for
  any repository, which does not define it.
  Understood values are

  .. program-output:: python -c "from repod.common.enums import CompressionTypeEnum; print('\"' + '\", \"'.join(e.value for e in CompressionTypeEnum) + '\"')"

* *management_repo*: A table setting a *directory* and an optional upstream
  *url* string which serves as the *management repository* for any repository,
  which does not define it. Each configured repository is represented as a
  subdirectory structure in the management repository. Many repositories can
  share the same *management_repo*.

* *package_pool*: A string setting a directory that serves as the package pool
  for any repository, which does not define it.

* *package_verification*: An optional string setting the implementation of the
  package signature verification for all repositories.
  If a signature verification implementation is selected, packages that are
  added to the repository must be signed.
  Understood values are

  .. program-output:: python -c "from repod.common.enums import PkgVerificationTypeEnum; print('\"' + '\", \"'.join(e.value for e in PkgVerificationTypeEnum) + '\"')"

* *source_pool*: A string setting a directory that serves as the source tarball
  pool for any repository, which does not define it.

.. _repod.conf_syncdb_settings:

SYNC DATABASE SETTINGS
----------------------

Sync database settings offer control over the way data for repository sync
databases is exported. For any undefined option defaults are assumed (see
:ref:`repod.conf_default_options`).

* *desc_version*: An integer setting the desc version used when exporting the
  management repository to a repository sync database.
  Understood values are

  .. program-output:: python -c "from repod.common.enums import PackageDescVersionEnum; print(', '.join(str(e.value) for e in PackageDescVersionEnum))"

* *files_version*: An integer setting the files version used when exporting the
  management repository to a repository sync database.
  Understood values are

  .. program-output:: python -c "from repod.common.enums import FilesVersionEnum; print(', '.join(str(e.value) for e in FilesVersionEnum))"

.. _repod.conf_repository_options:

REPOSITORY OPTIONS
------------------

Repository options are used to configure a specific repository. If optional
options are not defined, global options (see :ref:`repod.conf_global_options`)
or defaults (see :ref:`repod.conf_default_options`) are assumed.

* *architecture* (optional): A string setting the CPU architecture.
  Understood values are

  .. program-output:: python -c "from repod.common.enums import ArchitectureEnum; print('\"' + '\", \"'.join([arch.value for arch in ArchitectureEnum]) + '\"')"

* *database_compression* (optional): A string setting the database compression used for
  the repository.
  Understood values are

  .. program-output:: python -c "from repod.common.enums import CompressionTypeEnum; print('\"' + '\", \"'.join(e.value for e in CompressionTypeEnum) + '\"')"

* *management_repo* (optional): A table setting a *directory* and an optional
  upstream *url* string which serves as the *management repository* for the
  repository. Each configured repository is represented as a subdirectory
  structure in the management repository. Many repositories can share the same
  *management_repo*.

* *name*: A string setting the name of the repository. It is used as the
  location to store stable package data of the repository.
  The *name* and *architecture* combination **must be unique**.
  If the string denotes a relative directory it is used below the default
  package repository base directory (see
  :ref:`repod.conf_default_directories`).

  If the string denotes an absolute directory it is used directly and the
  default base directory is disregarded.

* *package_pool* (optional): A string setting a directory that serves as the
  package pool for the repository. If repositories move packages amongst one
  another, they need to use the same *package_pool*.

* *source_pool* (optional): A string setting a directory that serves as the
  source tarball pool for the repository. If repositories move packages amongst
  one another, they need to use the same *package_pool*.

* *staging* (optional): A string setting the staging name of the repository. It
  is used as the location to store staging package data of the repository.
  Multiple repositories may use the same *stable* and *architecture*
  combination. If the string denotes a relative directory it is used below the
  default package repository base directory (see
  :ref:`repod.conf_default_directories`).

  If the string denotes an absolute directory it is used directly and the
  default base directory is disregarded.

* *testing* (optional): A string setting the testing name of the repository. It
  is used as the location to store testing package data of the repository.
  Multiple repositories may use the same *stable* and *architecture*
  combination. If the string denotes a relative directory it is used below the
  default package repository base directory (see
  :ref:`repod.conf_default_directories`).

  If the string denotes an absolute directory it is used directly and the
  default base directory is disregarded.

.. _repod.conf_defaults:

DEFAULTS
--------

If no configuration is provided, a repository named "default", with management
repository, but without staging or testing repository, using default
directories and default options is created automatically. This roughly
evaluates to the following configuration:

.. code:: toml

  architecture = "any"
  database_compression = "gz"

  [syncdb_settings]
  desc_version = 1
  files_version = 1

  [management_repo]
  directory = "default"

  [[repositories]]
  name = "default"

.. _repod.conf_default_directories:

DEFAULT DIRECTORIES
^^^^^^^^^^^^^^^^^^^

* *$XDG_STATE_HOME/repod/management/* The default per-user location below which
  management repository directories are created (aka management repository base
  directory).

* */var/lib/repod/management/* The default system-wide location below which
  management repository directories are created (aka management repository base
  directory).

* *$XDG_STATE_HOME/repod/data/pool/package/* The default per-user location
  below which package pool directories are created (aka. package pool base
  directory).

* */var/lib/repod/data/pool/package/* The default system-wide location below
  which package pool directories are created (aka. package pool base
  directory).

* *$XDG_STATE_HOME/repod/data/repo/package/* The default per-user location
  below which package repository directories are created (aka. package
  repository base directory).

* */var/lib/repod/data/repo/package/* The default system-wide location below
  which package repository directories are created (aka. package repository
  base directory).

* *$XDG_STATE_HOME/repod/data/pool/source/* The default per-user location below
  which source pool directories are created (aka. source pool base directory).

* */var/lib/repod/data/pool/source/* The default system-wide location below
  which source pool directories are created (aka. source pool base directory).

* *$XDG_STATE_HOME/repod/data/repo/source/* The default per-user location below
  which source repository directories are created (aka. source repository base
  directory).

* */var/lib/repod/data/repo/source/* The default system-wide location below
  which source repository directories are created (aka. source repository base
  directory).

.. _repod.conf_default_options:

DEFAULT OPTIONS
^^^^^^^^^^^^^^^

* The default CPU architecture if neither global nor per-repository
  *architecture* is defined:

  .. program-output:: python -c "from repod.config.defaults import DEFAULT_ARCHITECTURE; print('\"' + DEFAULT_ARCHITECTURE.value + '\"')"

* The default database compression if neither global nor per-repository
  *database_compression* is defined:

  .. program-output:: python -c "from repod.config.defaults import DEFAULT_DATABASE_COMPRESSION; print('\"' + DEFAULT_DATABASE_COMPRESSION.value + '\"')"

* The default repository *name* if no repository is defined:

  .. program-output:: python -c "from repod.config.defaults import DEFAULT_NAME; print('\"' + DEFAULT_NAME + '\"')"

* The default *desc_version* for sync databases if none is defined:

  .. program-output:: python -c "from repod.common.enums import PackageDescVersionEnum; print(PackageDescVersionEnum.DEFAULT.value)"

* The default *files_version* for sync databases if none is defined:

  .. program-output:: python -c "from repod.common.enums import FilesVersionEnum; print(FilesVersionEnum.DEFAULT.value)"

EXAMPLES
--------

Example 1. One repository with custom architecture
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: toml

  [[repositories]]
  architecture = "x86_64"
  name = "repo"
  staging = "repo-staging"
  testing = "repo-testing"

Example 2. Two repositories with shared staging and testing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: toml

  [[repositories]]
  architecture = "x86_64"
  name = "repo1"
  staging = "repo-staging"
  testing = "repo-testing"

  [[repositories]]
  architecture = "x86_64"
  name = "repo2"
  staging = "repo-staging"
  testing = "repo-testing"

Example 3. One repository with custom management repo
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: toml

  [[repositories]]
  architecture = "x86_64"
  name = "repo1"
  staging = "repo-staging"
  testing = "repo-testing"
  [management_repo]
  directory = "custom_management"
  url = "ssh://user@custom-upstream.tld/repository.git"

Example 4. One repository with non-standard directories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: toml

  [[repositories]]
  architecture = "x86_64"
  name = "/absolute/path/to/repo1"
  staging = "/absolute/path/to/repo-staging"
  testing = "/absolute/path/to/repo-testing"
  [management_repo]
  directory = "/absolute/path/to/management_repo"

Example 5. One repository with pacman-key based signature verification
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: toml

  package_verification = "pacman-key"

  [[repositories]]
  architecture = "x86_64"
  name = "repo1"
  debug = "repo-debug"
  staging = "repo-staging"
  testing = "repo-testing"

SEE ALSO
--------

``repod-file(1)``, ``pacman(8)``, ``pacman-key(8)``
