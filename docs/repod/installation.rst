.. _installation:

============
Installation
============

Repod is available on the Python Package Index (PyPi):
https://pypi.org/project/repod/

You can install the latest released version of repod by executing

.. code:: sh

  pip install repod

Requirements
------------

Installing repod automatically installs its dependencies as well.

A few optional dependencies offer different functionality over the defaults.

Pyalpm
^^^^^^

By default repod makes use of an internal implementation of |vercmp|. If |pyalpm|
is detected it is used for version comparison instead.

Python-magic
^^^^^^^^^^^^

By default repod makes use of |python-magic| for file type detection. If
``file-magic`` (provided by |file|) is detected, it is used instead.

Development environment
-----------------------

The repod project can be used from a git clone of the project, with the help of
|poetry|.

.. code:: sh

  git clone https://gitlab.archlinux.org/archlinux/repod/
  cd repod
  poetry install

Afterwards it is possible to make use of existing :ref:`tooling` with the help
of ``poetry run`` (e.g. ``poetry run repod-file --help``).

.. |vercmp| raw:: html

  <a target="blank" href="https://man.archlinux.org/man/vercmp.8">vercmp</a>

.. |pyalpm| raw:: html

  <a target="blank" href="https://pypi.org/project/pyalpm/">pyalpm</a>

.. |python-magic| raw:: html

  <a target="blank" href="https://pypi.org/project/python-magic/">python-magic</a>

.. |file| raw:: html

  <a target="blank" href="https://darwinsys.com/file/">file</a>

.. |poetry| raw:: html

  <a target="blank" href="https://python-poetry.org/">poetry</a>
