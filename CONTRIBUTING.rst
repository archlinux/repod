============
Contributing
============

These are the contribution guidelines for arch-repo-management.
All code contributions fall under the terms of the GPL-3.0-or-later (see
`LICENSE`_).

Please read our distribution-wide `Code of Conduct`_ before contributing, to
understand what actions will and will not be tolerated.

Development of arch-repo-management takes place on Arch Linux' Gitlab:
https://gitlab.archlinux.org/archlinux/arch-repo-management.

Discussion
==========

Discussion around arch-repo-management may take place on the `arch-projects
mailing list`_ and in `#archlinux-projects`_ on `Libera Chat`_.

All past and present authors of archlinux-repo-management are listed in `AUTHORS`_.

Requirements
============

The following packages need to be installed to be able to lint and develop this
project:

* python-tox

An `editorconfig`_ file is provided in this repository and the text editor in
use should be configured to make use of it.

Additional helpful integrations for linting and typing are:

* python-isort
* flake8
* mypy

arch-repo-management
====================

The **arch-repo-management** project is written in typed python.

The code base is type checked, linted and formatted using standardized tooling.
Please make sure to run ``tox -e linter`` before providing a merge request.

Testing
=======

Test cases are developed per module in the `tests`_ directory using `pytest`_
and should consist of atomic single expectation tests.
Huge test cases asserting various different expectations are discouraged and
should be split into finer grained test cases or covered using `parametrized
tests`_.

The tests are distinguished between *coverage tests* and *integration tests*.
While the former are meant to target what is commonly referred to as *unit
tests*, the latter are meant to test more complex scenarios, involving actual
repository actions, etc.

To execute all coverage tests use

.. code:: sh

   tox -e coverage

To run all integration tests use

.. code:: sh

   tox -e integration

.. _LICENSE: LICENSE
.. _Code of Conduct: https://terms.archlinux.org/docs/code-of-conduct/
.. _arch-projects mailing list: https://lists.archlinux.org/listinfo/arch-projects
.. _#archlinux-projects: ircs://irc.libera.chat/archlinux-projects
.. _Libera Chat: https://libera.chat/
.. _AUTHORS: AUTHORS.rst
.. _editorconfig: https://editorconfig.org/
.. _tests: tests
.. _pytest: https://docs.pytest.org/
.. _parametrized tests: https://docs.pytest.org/en/latest/how-to/parametrize.html
