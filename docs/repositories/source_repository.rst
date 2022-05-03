.. _source repository:

=================
Source Repository
=================

A source repository is a |version control repository|, that contains the
necessary files to build a package. At the bare minimum this includes a
|PKGBUILD| file, but may contain an install script as well as patches or other
arbitrary files.

Using |makepkg|, the sources are used to build a package, which can be
installed with |pacman|. With the help of |package splitting| it is possible to
create more than one package from a single |PKGBUILD|.

.. note::

  Due to |dbscripts| and |makepkg| limitations it is currently not possible to
  target more than one :ref:`binary repository` with a single |PKGBUILD|.

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
