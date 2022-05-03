.. _installation:

============
Installation
============

The repod project can be used from a git clone of the project, with the help of
|poetry|.

.. note::

  At the time of writing, the project is not yet available on https://pypi.org
  and therefore can not be installed using ``pip``.

.. code:: sh

  git clone https://gitlab.archlinux.org/archlinux/arch-repo-management/
  cd arch-repo-management
  poetry install

Afterwards it is possible to make use of existing :ref:`tooling` with the help
of ``poetry run`` (e.g. ``poetry run db2json --help`` or ``poetry run json2db
--help``).

.. |poetry| raw:: html

  <a target="blank" href="https://python-poetry.org/">poetry</a>
