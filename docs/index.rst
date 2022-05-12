===================
repod documentation
===================

The repod project contains tooling to maintain binary package repositories for
Linux distributions using the |pacman| package manager.

It is developed at https://gitlab.archlinux.org/archlinux/repod

.. note::

   Repod is still in a pre-release state. Aside from test and development
   setups it should not yet be used in a production environment!

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
   repod/tooling.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. |pacman| raw:: html

  <a target="blank" href="https://archlinux.org/pacman/">pacman</a>
