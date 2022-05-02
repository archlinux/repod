====
Desc
====

Repository sync databases contain per-package ``desc`` files, that carry
identifiers and their values, which serve to describe a package.

Identifiers are composed of a string in all capital letters ``[A-Z]`` with a
leading and a trailing ``%`` character.
All identifiers as well as values are provided on a per-line basis in a
``desc`` file, leaving an empty line between each identifier/value pair.

Identifiers may be required or optional. As requirements change over time and
identifiers and their values may be added or removed, the ``desc`` files are
distinguished using the below versioning.

Desc v1
-------

* ``%ARCH%`` (**required**): The CPU architecture of the package (one line
  below the identifier)
* ``%BACKUP%``: A list of package files to be backed up by the package manager
  (one file per line below the identifier)
* ``%BASE%`` (**required**): The ``pkgbase`` (see
  |PKGBUILD.5#PACKAGE_SPLITTING|) of a package (one line below the identifier)
* ``%BUILDDATE%`` (**required**): The time - in seconds since the epoch - when
  the package has been built (one line below the identifier)
* ``%CHECKDEPENDS%``: A list of package names required when running the
  ``check()`` function (see |PKGBUILD.5#PACKAGING_FUNCTIONS|) (one name per
  line below the identifier)
* ``%CONFLICTS%``: A list of package names that conflict with a package (one
  name per line below the identifier)
* ``%CSIZE%`` (**required**): The size - in Bytes - of the compressed package
  (one line below the identifier)
* ``%DEPENDS%``: A list of package names that a package depends on (one name
  per line below the identifier)
* ``%DESC%`` (**required**): The description of a package (one line below the
  identifier)
* ``%FILENAME%`` (**required**): The filename of a package file (one line below
  the identifier)
* ``%GROUPS%``: A list of package group names that a package belongs to (one
  name per line below the identifier)
* ``%ISIZE%`` (**required**): The size - in Bytes - of the package when
  installed (one line below the identifier)
* ``%LICENSE%`` (**required**): A list of license names that the files of a
  package are licensed under (one name per line below the identifier)
* ``%MAKEDEPENDS%``: A list of package names required when running the
  ``prepare()`` and/ or ``build()`` function (see
  |PKGBUILD.5#PACKAGING_FUNCTIONS|) (one name per line below the identifier)
* ``%MD5SUM%`` (**required**): The md5 checksum of the package file (one line
  below the identifier)
* ``%NAME%`` (**required**): The name of the package (one line below the
  identifier)
* ``%OPTDEPENDS%``: A list of package names that can be used optionally to
  extend a package's functionality (one name per line below the identifier)
* ``%PACKAGER%`` (**required**): The UID (name and e-mail address) of the
  packager who created a package (one line below the identifier)
* ``%PGPSIG%`` (**required**): The base64 encoded PGP signature of a package
  (one line below the identifier)
* ``%PROVIDES%``: A list of package names that a package provides (one name per
  line below the identifier)
* ``%REPLACES%``: A list of package names that a package replaces (one name per
  line below the identifier)
* ``%SHA256SUM%`` (**required**): The sha256 checksum of the package file (one
  line below the identifier)
* ``%URL%`` (**required**): The URL of the package (one line below the
  identifier)
* ``%VERSION%`` (**required**): The version string of the package (one line
  below the identifier)


.. |PKGBUILD.5#PACKAGE_SPLITTING| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/PKGBUILD.5#PACKAGE_SPLITTING">PKGBUILD.5#PACKAGE_SPLITTING</a>

.. |PKGBUILD.5#PACKAGING_FUNCTIONS| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/PKGBUILD.5#PACKAGING_FUNCTIONS">PKGBUILD.5#PACKAGING_FUNCTIONS</a>
