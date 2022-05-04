.. _configuration:

=============
Configuration
=============

The repod service uses a |TOML| based configuration file format.

A configuration can either be provided using ``/etc/repod.conf`` and/ or by
providing ``.conf`` files in the override location ``/etc/repod.conf.d/``. If
no configuration file exists, the application will assume some defaults.
Override configuration files are merged and used to override the defaults or
any configuration provided in the default configuration file.

.. _options and defaults:

Options and defaults
--------------------

.. _global options and defaults:

Global
^^^^^^

The configuration allows for setting global defaults (valid for all configured
repositories). Each repository will fall back to these in case there is no
repository-specific configuration provided.

* **architecture**: The CPU architecture, that is used for each :ref:`binary
  repository` if they do not define an **architecture** themselves (unset by
  default).
* **management_repo**: A *required* object describing a directory which
  contains the :ref:`management repository` (defaults to
  ``"/var/lib/repod/management/default/"``) and its upstream url
  (unset by default).
* **package_pool**: The directory which is used as :ref:`package pool`
  (defaults to ``"/var/lib/repod/pool/package/default/"``).
* **package_repo_base**: The directory which contains all :ref:`binary
  repository` directories (defaults to
  ``"/var/lib/repod/repo/"``).
* **source_pool**: The directory which is used as :ref:`source tarball pool`
  (defaults to ``"/var/lib/repod/pool/source/default/"``).
* **source_repo_base**: The directory which contains all :ref:`source tarball
  repository` directories (defaults to
  ``"/var/lib/repod/source/"``).

.. _repository options and defaults:

Repositories
^^^^^^^^^^^^

A list of repositories needs to be defined (a minimum of one is required). Each
repository can be configured to override some of the :ref:`global options and
defaults` options and defaults.


* **architecture**: The *optional* CPU architecture for the :ref:`binary
  repository`. If set, it is considered over the global default, else the
  global default is used.

  .. warning::

    An **architecture** must be set per repository, if none is set globally!

* **management_repo**: The *optional* object describing a directory that
  contains the :ref:`management repository` for the :ref:`binary repository`
  and its upstream url.
  If set, it is considered over the global default, else the global default is
  used.

  .. warning::

    A **management_repo** must be set per repository, if none is set globally!

* **name**: The *mandatory* name of the :ref:`binary repository`, which will be
  used to create a directory below **package_repo_base**.

  .. warning::

    A repository **name** and **architecture** combination must be unique among
    the list of repositories!

* **package_pool**: The *optional* directory that is used as :ref:`package
  pool` for the :ref:`binary repository`. If set, it is considered over the
  global default, else the global default is used.
* **source_pool**: The *optional* directory that is used as :ref:`source
  tarball pool` for the :ref:`source tarball repository`. If set, it is
  considered over the global default, else the global default is used.
* **staging**: The *optional* name of a directory which is used as a
  **staging** repository for the stable :ref:`binary repository` defined by
  **name**. Similar to the stable repository, the **staging** repository is
  created below **package_repo_base**.

  .. note::

    Although two repositories may share the same **staging** repository, it is
    not possible to use one repository's **staging** repository as another's
    **testing** repository.

* **testing**: The *optional* name of a directory which is used as a *testing**
  repository for the stable :ref:`binary repository` defined by **name**.
  Similar to the stable repository, the **testing** repository is created below
  **package_repo_base**.

  .. note::

    Although two repositories may share the same **testing** repository, it is
    not possible to use one repository's **testing** repository as another's
    **staging** repository.

.. _configuration examples:

Examples
--------

Defaults with one repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: toml

  architecture = "x86_64"
  management_repo = {directory = "/var/lib/repod/management/default", url = "https://foo.bar"}

  [[repositories]]
  name = "repo"
  staging = "repo-staging"
  testing = "repo-testing"

Defaults with multi-architecture repositories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: toml

  management_repo = {directory = "/var/lib/repod/management/default", url = "https://foo.bar"}

  [[repositories]]
  architecture = "x86_64"
  name = "repo"
  staging = "repo-staging"
  testing = "repo-testing"

  [[repositories]]
  architecture = "aarch64"
  name = "repo"
  staging = "repo-staging"
  testing = "repo-testing"

.. |TOML| raw:: html

  <a target="blank" href="https://en.wikipedia.org/wiki/TOML">TOML</a>
