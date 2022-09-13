.. _contributing:

============
Contributing
============

These are the contribution guidelines for repod.

Development of repod takes place on Arch Linux' Gitlab:
https://gitlab.archlinux.org/archlinux/repod.

Please read our distribution-wide `Code of Conduct
<https://terms.archlinux.org/docs/code-of-conduct/>`_ before contributing, to
understand what actions will and will not be tolerated.

License
=======

All code contributions fall under the terms of the `GPL-3.0-or-later
<https://www.gnu.org/licenses/gpl-3.0.html>`_.

All documentation contributions fall under the terms of the `GFDL-1.3-or-later
<https://www.gnu.org/licenses/fdl-1.3.html>`_.

All past and present authors of repod are listed in :ref:`authors`.

Discussion
==========

Discussion around repod takes place on the `arch-projects mailing list
<https://lists.archlinux.org/listinfo/arch-projects>`_ and in
`#archlinux-projects <ircs://irc.libera.chat/archlinux-projects>`_ on `Libera
Chat <https://libera.chat/>`_.

Writing code
============

The project is written in typed Python. Please refer to the `issue tracker
<https://gitlab.archlinux.org/archlinux/repod/-/issues>`_ for open tickets and
ongoing development.

`Tox <https://tox.readthedocs.io>`_ and `pdm <https://pdm.fming.dev/latest/>`_
need to be installed to be able to test the project's code and to generate its
user facing documentation.

The code base is type checked, linted and formatted using standardized tooling.
Please make sure to run ``tox`` before providing a merge request.

For all notable changes to the code base make sure to add a :ref:`changelog`
entry in the `[Unreleased]` section.

.. note::

  The changelog style follows the `keep a changelog
  <https://keepachangelog.com/en/1.0.0/>`_ methodology.

Valid subsection topics are:

* **Added** for new features.
* **Changed** for changes in existing functionality.
* **Deprecated** for soon-to-be removed features.
* **Removed** for now removed features.
* **Fixed** for any bug fixes.
* **Security** in case of vulnerabilities.

Integration for text editors
============================

An `editorconfig <https://editorconfig.org/>`_ file is provided in the code
repository repository and the text editor in use should be configured to make
use of it.

Additional helpful integrations for linting and type checking are:

* `flake8 <https://flake8.pycqa.org/en/latest/>`_
* `isort <https://pycqa.github.io/isort/>`_
* `mypy <https://mypy.readthedocs.io/en/stable/>`_

Documentation
=============

All code is documented following
`numpydoc <https://numpydoc.readthedocs.io/en/latest/>`_ (see the accompanying
`style guide <https://numpydoc.readthedocs.io/en/latest/format.html>`_ for
further info).

Writing tests
=============

Test cases are developed per module in the ``tests/`` directory using
`pytest <https://docs.pytest.org/>`_ and should consist of atomic single
expectation tests.
Huge test cases asserting various different expectations are discouraged and
should be split into finer grained test cases or covered using `parametrized
tests <https://docs.pytest.org/en/latest/how-to/parametrize.html>`_.

.. note::

  New code additions are not accepted below 100% test coverage.

The tests are distinguished between *coverage tests* and *integration tests*.
While the former are meant to target what is commonly referred to as *unit
tests*, the latter are meant to test more complex scenarios, involving actual
repository actions, etc.

To execute all coverage tests use

on Linux

.. code:: bash

  tox -e coverage-linux

on macOS

.. code:: bash

  tox -e coverage-macos

To run all integration tests use

.. code:: bash

  tox -e integration

Writing documentation
=====================

Documentation is written in `reStructuredText
<https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html>`_ and
assembled using `sphinx <https://www.sphinx-doc.org/en/master/contents.html>`_
in the ``docs/`` directory.

To build the documentation use

.. code:: bash

  tox -e docs
