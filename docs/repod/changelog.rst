.. _changelog:

=========
Changelog
=========

All notable changes to this project should be documented here.
For more detailed information have a look at the |git log|.

.. _version unreleased:

[Unreleased]
------------

Added
^^^^^

* Package verification based on ``pacman-key`` may be configured by setting the
  global configuration option ``package_verification`` to ``pacman-key``.
* A ``PackageDescV2`` which removes the ``%PGPSIG%`` identifier in the ``desc``
  files rendered from it. The default is still ``PackageDescV1`` (which
  provides the ``%PGPSIG%`` identifier), but users may already try the new
  functionality using the ``syncdb_settings.desc_version`` option in
  ``repod.conf`` (see ``man 5 repod.conf``).

Changed
^^^^^^^

* Extend ``OutputPackageBaseV1`` with optional ``.BUILDINFO`` data retrieved
  from packages using the new ``OutputBuildInfo`` (and child classes). This
  adds a relevant subset of ``.BUILDINFO`` files to the management repository.

[0.1.0] - 2022-07-02
--------------------

Changed
^^^^^^^

* Documentation on installation and dependencies.

[0.1.0-alpha1] - 2022-07-01
---------------------------

Added
^^^^^

* Functionality to validate package files in accordance with current versions
  of ``.BUILDINFO``, ``.MTREE`` and ``.PKGINFO`` files.
* Functionality to validate repository sync databases in accordance with
  current versions of ``desc`` and ``files`` files found in the default and
  files sync databases.
* Functionality to describe the contents of repository sync databases in the
  context of a management repository consisting of JSON files per ``pkgbase``.
* Functionality to export JSON schema which can be used to validate existing
  functionality and data formats.
* A self-validating configuration layer which will be used in upcoming versions
  of the project to allow configuration of a ``repod`` service.
* The commandline utility ``repod-file`` to expose existing functionality for
  package inspection, data transformation and JSON schema export.
* Documentation on internals of the project and the ``repod-file`` commandline
  utility.
* Manual page for ``repod-file``.

.. |git log| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/git-log.1">git log</a>
