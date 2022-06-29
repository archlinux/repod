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

  git clone https://gitlab.archlinux.org/archlinux/repod/
  cd repod
  poetry install

Afterwards it is possible to make use of existing :ref:`tooling` with the help
of ``poetry run`` (e.g. ``poetry run repod-file --help``).

.. |poetry| raw:: html

  <a target="blank" href="https://python-poetry.org/">poetry</a>
