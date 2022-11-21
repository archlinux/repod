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

A *TOML [1]* based configuration file, which can be provided in a default
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

* *archiving*: An optional table or boolean value, which defines the archiving
  options used for any repository, that do not define them explicitly.
  When unset or set to *true*, default archiving options are created. If set to
  *false*, archiving is disabled by default, but may still be set per
  repository.
  When defined as a table, the option has to define the following key-value pairs:

  * *packages*: The name of the *package archive directory* (see
    :ref:`repod.conf_default_directories` for default values), below which
    directory structures and files for package and signature file archiving are
    created.
    This directory must be absolute.

  * *sources*: The name of the *source archive directory* (see
    :ref:`repod.conf_default_directories` for default values), below which
    directory structures and files for source tarball archiving are created.
    This directory must be absolute.

* *build_requirements_exist*: An optional boolean value, which defines whether
  the build requirements of added packages must exist in the archive (if
  configured), any of the stability layers of the target repository or the set
  of packages being added.
  When unset, the value will be set to the default (see
  :ref:`repod.conf_default_options`).
  When set to *false*, the build requirements of added packages are not
  checked, when set to *true*, they are checked.
  This setting may still be overriden per repository.

* *database_compression*: A string setting the database compression used for
  any repository, which does not define it.
  Understood values are

  .. program-output:: python -c "from repod.common.enums import CompressionTypeEnum; print('\"' + '\", \"'.join(e.value for e in CompressionTypeEnum) + '\"')"

* *management_repo*: A table providing configuration for the *management
  repository* for any repository, which does not define one explicitly.
  As each configured binary package repository is represented as a subdirectory
  structure in the management repository, several repositories can share the
  same *management_repo*.

  * *directory*: The name of the management repository in the *management
    repository base directory* (see *DEFAULT DIRECTORIES*), below which per
    binary package repository directories are created. If the string denotes an
    absolute directory it is used directly and the default base directory is
    disregarded.

  * *json_dumps*: An integer, defining the option for orjson's dumps() method
    (see https://github.com/ijl/orjson#option). Defaults to:

    .. program-output:: python -c "from repod.config.defaults import ORJSON_OPTION; print(ORJSON_OPTION)"

  * *url*: An optional url string, for the upstream repository of the management repository (currently not used)

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

**NOTE**: The resolved directories for repositories must be globally unique.
The only exceptions to this rule are *package_pool*, *source_pool*,
*archiving.packages* and *archiving.sources*.

* *architecture* (optional): A string setting the CPU architecture.
  Understood values are

  .. program-output:: python -c "from repod.common.enums import ArchitectureEnum; print('\"' + '\", \"'.join([arch.value for arch in ArchitectureEnum]) + '\"')"

* *archiving*: An optional table or boolean value, which defines the archiving
  options.
  When unset or set to *true*, the global archiving options are used. If set to
  *false*, archiving is disabled.

  **NOTE**: When repositories are used together, they should be using the same archiving options.

  When defined as a table, the option has to define the following key-value pairs:

  * *packages*: The name of the *package archive directory* (see
    :ref:`repod.conf_default_directories` for default values), below which
    directory structures and files for package and signature file archiving are
    created.
    This directory must be absolute.

  * *sources*: The name of the *source archive directory* (see
    :ref:`repod.conf_default_directories` for default values), below which
    directory structures and files for source tarball archiving are created.
    This directory must be absolute.

* *build_requirements_exist*: An optional boolean value, which defines whether
  the build requirements of added packages must exist in the archive (if
  configured), any of the stability layers of the target repository or the set
  of packages being added.
  When unset, the value will be set to the value defined globally.
  When set to *false*, the build requirements of added packages are not
  checked, when set to *true*, they are checked.

* *database_compression* (optional): A string setting the database compression used for
  the repository.
  Understood values are

  .. program-output:: python -c "from repod.common.enums import CompressionTypeEnum; print('\"' + '\", \"'.join(e.value for e in CompressionTypeEnum) + '\"')"

* *management_repo* (optional): An inline table providing configuration for the
  *management repository* of the repository. If it is provided, it has
  precedence over a globally defined *management_repo*. As each configured
  repository is represented as a subdirectory structure in the management
  repository, several repositories can share the same *management_repo*.

  * *directory*: The name of the management repository in the *management
    repository base directory* (see *DEFAULT DIRECTORIES*), below which per
    binary package repository directories are created. If the string denotes an
    absolute directory it is used directly and the default base directory is
    disregarded.

  * *json_dumps*: An integer, defining the option for orjson's dumps() method
    (see https://github.com/ijl/orjson#option). Defaults to:

    .. program-output:: python -c "from repod.config.defaults import ORJSON_OPTION; print(ORJSON_OPTION)"

  * *url*: An optional url string, for the upstream repository of the management repository (currently not used)

* *package_url_validation* (optional): An inline table providing configuration
  for the validation of source URLs. Source URLs are links, that may be
  provided per pkgbase using *repod-file* and serve as reference to the source
  files (e.g. PKGBUILD) for each package.

  * *urls*: A list of URL strings, against which the source URLs provided to
    *repod-file* must validate.
  * *tls_required*: A boolean value, setting whether the URLS in the *urls*
    list and any source URL provided to *repod-file* must use TLS or not.

* *name*: A string setting the name of the repository. It is used to construct
  the location below which stable package data of the repository is stored.

  **NOTE**: The *name* and *architecture* combination **must be unique**.

  If the string denotes a relative directory it is used below the default
  *package repository base directory* and *management repository base
  directory* (see :ref:`repod.conf_default_directories`).

  If the string denotes an absolute directory it is used directly and the
  default base directories are disregarded.

* *debug*: A string setting the debug name of the repository. It is used to
  construct the location below which stable debug package data of the
  repository is stored.

  **NOTE**: When using this option and also using the *staging* or *testing*
  options, the *staging_debug* and *testing_debug* options (respectively) must
  be set as well.

  If the string denotes a relative directory it is used below the default
  *package repository base directory* and *management repository base
  directory* (see :ref:`repod.conf_default_directories`).

  If the string denotes an absolute directory it is used directly and the
  default base directories are disregarded.

* *package_pool* (optional): A string setting a directory that serves as the
  package pool for the repository.

  **NOTE**: If repositories move packages amongst one another, they need to use
  the same *package_pool*.

  If the string denotes a relative directory it is used below the default
  *package pool base directory* (see :ref:`repod.conf_default_directories`).

  If the string denotes an absolute directory it is used directly and the
  default base directories are disregarded.

* *source_pool* (optional): A string setting a directory that serves as the
  source tarball pool for the repository.

  **NOTE**: If repositories move packages amongst one another, they need to use
  the same *package_pool*.

  If the string denotes a relative directory it is used below the default
  *source pool base directory* (see :ref:`repod.conf_default_directories`).

  If the string denotes an absolute directory it is used directly and the
  default base directories are disregarded.

* *staging* (optional): A string setting the staging name of the repository. It
  is used to construct the location below which staging package data of the
  repository is stored.

  If the string denotes a relative directory it is used below the
  default *package repository base directory* and *management repository base
  directory* (see :ref:`repod.conf_default_directories`).

  If the string denotes an absolute directory it is used directly and the
  default base directories are disregarded.

* *staging_debug* (optional): A string setting the staging debug name of the
  repository. It is used to construct the location below which staging debug
  package data of the repository is stored.

  **NOTE**: The *staging* and *debug* option must be set when using this
  option. Similarly, if *debug* and *staging* are configured for a repository,
  this option also has to be configured.

  If the string denotes a relative directory it is used below the
  default *package repository base directory* and *management repository base
  directory* (see :ref:`repod.conf_default_directories`).

  If the string denotes an absolute directory it is used directly and the
  default base directories are disregarded.

* *testing* (optional): A string setting the testing name of the repository. It
  is used to construct the location below which testing package data of the
  repository is stored.

  If the string denotes a relative directory it is used below the
  default *package repository base directory* and *management repository base
  directory* (see :ref:`repod.conf_default_directories`).

  If the string denotes an absolute directory it is used directly and the
  default base directories are disregarded.

* *testing_debug* (optional): A string setting the testing debug name of the
  repository. It is used to construct the location below which testing debug
  package data of the repository is stored.

  **NOTE**: The *testing* and *debug* option must be set when using this
  option. Similarly, if *debug* and *testing* are configured for a repository,
  this option also has to be configured.

  If the string denotes a relative directory it is used below the
  default *package repository base directory* and *management repository base
  directory* (see :ref:`repod.conf_default_directories`).

  If the string denotes an absolute directory it is used directly and the
  default base directories are disregarded.

.. _repod.conf_defaults:

DEFAULTS
--------

If no configuration is provided, a repository named "default", with management
repository, but without staging or testing repository, using default
directories and default options is created automatically. This roughly
evaluates to the following configuration:

.. code:: toml

  architecture = "any"
  archiving = true
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
  management repository directories are created (aka *management repository base
  directory*).

* */var/lib/repod/management/* The default system-wide location below which
  management repository directories are created (aka *management repository base
  directory*).

* *$XDG_STATE_HOME/repod/archive/package/* The default per-user location below
  which directory structures and files for package and signature file archiving
  are created (aka *package archive directory*).

* */var/lib/repod/archive/package/* The default system-wide location below
  which directory structures and files for package and signature file archiving
  are created (aka *package archive directory*).

* *$XDG_STATE_HOME/repod/archive/source/* The default per-user location below
  which directory structures and files for source tarball archiving are created
  (aka *source archive directory*).

* */var/lib/repod/archive/source/* The default system-wide location below which
  directory structures and files for source tarball archiving are created (aka
  *source archive directory*).

* *$XDG_STATE_HOME/repod/data/pool/package/* The default per-user location
  below which package pool directories are created (aka *package pool base
  directory*).

* */var/lib/repod/data/pool/package/* The default system-wide location below
  which package pool directories are created (aka *package pool base
  directory*).

* *$XDG_STATE_HOME/repod/data/repo/package/* The default per-user location
  below which package repository directories are created (aka *package
  repository base directory*).

* */var/lib/repod/data/repo/package/* The default system-wide location below
  which package repository directories are created (aka *package repository
  base directory*).

* *$XDG_STATE_HOME/repod/data/pool/source/* The default per-user location below
  which source pool directories are created (aka *source pool base directory*).

* */var/lib/repod/data/pool/source/* The default system-wide location below
  which source pool directories are created (aka *source pool base directory*).

* *$XDG_STATE_HOME/repod/data/repo/source/* The default per-user location below
  which source repository directories are created (aka *source repository base
  directory*).

* */var/lib/repod/data/repo/source/* The default system-wide location below
  which source repository directories are created (aka *source repository base
  directory*).

.. _repod.conf_default_options:

DEFAULT OPTIONS
^^^^^^^^^^^^^^^

* The default CPU architecture if neither global nor per-repository
  *architecture* is defined:

  .. program-output:: python -c "from repod.config.defaults import DEFAULT_ARCHITECTURE; print('\"' + DEFAULT_ARCHITECTURE.value + '\"')"

* The default value for checking build requirements of added packages, if
  *build_requirements_exist* not defined globally:

  .. program-output:: python -c "from repod.config.defaults import DEFAULT_BUILD_REQUIREMENTS_EXIST; print(str(DEFAULT_BUILD_REQUIREMENTS_EXIST).lower())"

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

Example 2. Two repositories with debug locations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: toml

  [[repositories]]
  architecture = "x86_64"
  name = "repo1"
  debug  = "repo1-debug"
  staging = "repo1-staging"
  staging_debug = "repo1-staging-debug"
  testing = "repo1-testing"
  testing_debug = "repo1-testing-debug"

  [[repositories]]
  architecture = "x86_64"
  name = "repo2"
  debug = "repo2-debug"
  staging = "repo2-staging"
  staging_debug = "repo2-staging-debug"
  testing = "repo2-testing"
  testing_debug = "repo2-testing-debug"

Example 3. One repository with custom management repo
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: toml

  [[repositories]]
  architecture = "x86_64"
  name = "repo1"
  staging = "repo-staging"
  testing = "repo-testing"
  management_repo = {directory = "custom_management", url = "ssh://user@custom-upstream.tld/repository.git"}

Example 4. One repository with non-standard directories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: toml

  [[repositories]]
  architecture = "x86_64"
  name = "/absolute/path/to/repo1"
  staging = "/absolute/path/to/repo-staging"
  testing = "/absolute/path/to/repo-testing"
  management_repo = {directory = "/absolute/path/to/management_repo"}

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

Example 6. One repository with source URL validation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: toml

  [[repositories]]
  architecture = "x86_64"
  name = "repo1"
  debug = "repo-debug"
  staging = "repo-staging"
  testing = "repo-testing"
  package_url_validation = {urls = ["https://custom.tld"], tls_required = true}

Example 6. One repository without archiving
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: toml

  [[repositories]]
  architecture = "x86_64"
  archiving = false
  name = "repo1"

Example 7. One repository without checks for build requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: toml

  [[repositories]]
  architecture = "x86_64"
  build_requirements_exist = false
  name = "repo1"

SEE ALSO
--------

:manpage:`repod-file(1)`, :manpage:`PKGBUILD(5)`, :manpage:`pacman(8)`, :manpage:`pacman-key(8)`

NOTES
-----

1. TOML specification

   https://toml.io/en/v1.0.0
