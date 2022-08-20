.. _changelog:

=========
Changelog
=========

All notable changes to this project should be documented here.
For more detailed information have a look at the |git log|.

.. _version unreleased:

[Unreleased]
------------

[0.2.0] - 2022-08-22
--------------------

Added
^^^^^

* Man page for ``repod.conf``.
* Per repository debug repository handling in configuration layer and CLI.
* Package verification based on ``pacman-key`` may be configured by setting the
  global configuration option ``package_verification`` to ``pacman-key``.
* A ``PackageDescV2`` which removes the ``%PGPSIG%`` identifier in the ``desc``
  files rendered from it. The default is still ``PackageDescV1`` (which
  provides the ``%PGPSIG%`` identifier), but users may already try the new
  functionality using the ``syncdb_settings.desc_version`` option in
  ``repod.conf`` (see ``man 5 repod.conf``).
* The ``repod.repo.package.repofile`` module provides functionality for file
  operations on repository files (e.g. package files or package signature
  files). The ``RepoFile`` class allows moving, copying, symlinking and
  removing of files.
* The ``repod-file repo importpkg`` subcommand which supersedes ``repod-file
  package import``, while also implementing the addition of package files (and
  optionally their signatures) to a given repository's package pool directory
  and creating the symlinks for them in the repository's package repository
  directory.
* A justfile for installing directories required for system mode and man pages.
* The ``repod-file repo importdb``, ``repod-file repo importpkg`` and
  ``repod-file repo writedb`` commands now accept a ``-a``/ ``--architecture``
  flag to define the target repository architecture, if repositories of the
  same name but differing CPU architectures exist.

Changed
^^^^^^^

* Configuration layer is now used in the CLI and required directories for
  repositories and data are automatically created upon launching it. The
  configuration layer distinguishes between system-wide and per-user locations.
* Extend ``OutputPackageBaseV1`` with optional ``.BUILDINFO`` data retrieved
  from packages using the new ``OutputBuildInfo`` (and child classes). This
  adds a relevant subset of ``.BUILDINFO`` files to the management repository.
* The ``repod-file`` subcommand ``management`` is renamed to ``repo`` and its
  subsubcommands ``import`` and ``export`` are renamed to ``importdb`` and
  ``writedb`` (respectively).
  The ``repod-file repo writedb`` command only accepts the name of the target
  repository and no target file anymore, as the repository sync database files
  are written to the binary package directory of the target repository.
* The email validation done for the ``Packager`` model does not by default
  check for deliverability anymore. In the future this is supposed to become
  configurable.
* The database compression of repositories can now only be set in the
  configuration file.

Fixed
^^^^^

* ``.PKGINFO`` values with equal signs are now handled correctly (e.g., equal
  signs in descriptions of ``optdepends`` entries).
* The ``usersettings`` fixture no longer leaks test state into the user system.
* The calculation of ``SHA-256`` checksums for packages in
  ``repod.file.package.Package.from_file`` were not done correctly, because
  after a previous ``MD5`` checksum calculation the package file was not read
  in its entirety.
* Fix file mode validation for ``.MTREE`` files.
* Fix path validation for ``.MTREE`` files.
* The conversion of special characters in octal representation in the ``mtree``
  files did not work for non-English unicode characters (e.g. cyrillic) and
  attempting to import packages that contain file names with such characters
  would fail.
* Some of the online documentation did not reflect the current state of the CLI
  anymore, so all information for the ``repod-file`` has been consolidated with
  its man page.

Removed
^^^^^^^

* The ``repod-file`` subcommand ``syncdb`` is removed due to being the reverse
  pendant to the ``management`` command.
* The ``repod-file package import`` subcommand as it is superseded by
  ``repod-file repo importpkg``.

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
