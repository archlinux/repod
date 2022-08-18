===================
repod documentation
===================

The repod project contains tooling to maintain binary package repositories for
Linux distributions using the |pacman| package manager.

It is developed at https://gitlab.archlinux.org/archlinux/repod

.. warning::

   Repod is still considered |alpha|. Aside from test and development setups it
   is strongly recommended to not use it in a production environment at this
   point!

.. toctree::
   :maxdepth: 2
   :caption: Repositories

   repositories/source_repository.rst
   repositories/source_tarball_repository.rst
   repositories/binary_repository.rst
   repositories/sync_database.rst
   repositories/management_repository.rst

.. toctree::
   :maxdepth: 2
   :caption: Packages

   packages/contents.rst
   packages/signatures.rst

.. toctree::
   :maxdepth: 2
   :caption: Using Repod

   repod/installation.rst
   repod/configuration.rst
   repod/man/index.rst
   repod/changelog.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. |pacman| raw:: html

  <a target="blank" href="https://archlinux.org/pacman/">pacman</a>

.. |alpha| raw:: html

  <a target="blank" href="https://en.wikipedia.org/wiki/Software_release_life_cycle#Alpha">alpha</a>
