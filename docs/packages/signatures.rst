.. _package signature:

=================
Package Signature
=================

To enable |pacman| to verify a package (see |package and database signature
checking|), a package file may be cryptographically signed by its packager or
an automated process.

.. _detached PGP signature:

Detached PGP signature
----------------------

Detached PGP signatures (see |gpg --detach-sign|) in binary form (see |gpg
--no-armor|) with a ``.sig`` suffix are supported.
They are provided next to the package file (e.g.
``package-1.0.0-1-any.pkg.tar.zst`` and
``package-1.0.0-1-any.pkg.tar.zst.sig``).

.. |pacman| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/pacman.8.en">pacman</a>

.. |package and database signature checking| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/pacman.conf.5#PACKAGE_AND_DATABASE_SIGNATURE_CHECKING">package and database signature checking</a>

.. |gpg --detach-sign| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/gpg.1#detach-sign">gpg --detach-sign</a>

.. |gpg --no-armor| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/gpg.1#no-armor">gpg --no-armor</a>
