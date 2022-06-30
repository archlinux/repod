# Contributing

These are the contribution guidelines for repod.

Development of repod takes place on Arch Linux' Gitlab:
https://gitlab.archlinux.org/archlinux/repod.

Please read our distribution-wide [Code of
Conduct](https://terms.archlinux.org/docs/code-of-conduct/) before
contributing, to understand what actions will and will not be tolerated.

## License

All code contributions fall under the terms of the **GPL-3.0-or-later** (see
[LICENSE](LICENSE)).

All documentation contributions fall under the terms of the
**GFDL-1.3-or-later** (see [docs/LICENSE](docs/LICENSE)).

All past and present authors of repod are listed in [AUTHORS.md](AUTHORS.md).

## Discussion

Discussion around repod takes place on the [arch-projects mailing
list](https://lists.archlinux.org/listinfo/arch-projects) and in
[#archlinux-projects](ircs://irc.libera.chat/archlinux-projects) on [Libera
Chat](https://libera.chat/).

## Writing code

The project is written in typed Python. Please refer to [issue
tracker](https://gitlab.archlinux.org/archlinux/repod/-/issues) for open
tickets and ongoing development.

[Tox](https://tox.readthedocs.io) and [poetry](https://python-poetry.org/) need
to be installed to be able to test the project's code and to generate its user
facing documentation.

The code base is type checked, linted and formatted using standardized tooling.
Please make sure to run ``tox`` before providing a merge request.

For all notable changes to the code base make sure to add a
[changelog](CHANGELOG.rst) entry in the `[Unreleased]` section. The changelog
style follows the ["keep a changelog"](https://keepachangelog.com/en/1.0.0/)
methodology. Valid subsection topics are:
* **Added** for new features.
* **Changed** for changes in existing functionality.
* **Deprecated** for soon-to-be removed features.
* **Removed** for now removed features.
* **Fixed** for any bug fixes.
* **Security** in case of vulnerabilities.

### Integration for text editors

An [editorconfig](https://editorconfig.org/) file is provided in this
repository and the text editor in use should be configured to make use of it.

Additional helpful integrations for linting and type checking are:

* [flake8](https://flake8.pycqa.org/en/latest/)
* [isort](https://pycqa.github.io/isort/)
* [mypy](https://mypy.readthedocs.io/en/stable/)

### Documentation

All code is documented following
[numpydoc](https://numpydoc.readthedocs.io/en/latest/) (see the accompanying
[style guide](https://numpydoc.readthedocs.io/en/latest/format.html) for
further info).

## Writing tests

Test cases are developed per module in the [tests](tests/) directory using
[pytest](https://docs.pytest.org/) and should consist of atomic single
expectation tests.
Huge test cases asserting various different expectations are discouraged and
should be split into finer grained test cases or covered using [parametrized
tests](https://docs.pytest.org/en/latest/how-to/parametrize.html).

New code additions are not accepted below 100% test coverage.

The tests are distinguished between *coverage tests* and *integration tests*.
While the former are meant to target what is commonly referred to as *unit
tests*, the latter are meant to test more complex scenarios, involving actual
repository actions, etc.

To execute all coverage tests use

```
tox -e coverage
```

To run all integration tests use

```
tox -e integration
```

## Writing documentation

Documentation is written in
[reStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html)
and assembled using
[sphinx](https://www.sphinx-doc.org/en/master/contents.html) in the
[docs](docs/) directory.

To build the documentation use

```
tox -e docs
```
