# repod
This project contains tooling to maintain binary package repositories for Linux
distributions using the [pacman](https://archlinux.org/pacman/) package manager.

**NOTE**: Repod is still in pre-release state and as such has not yet reached
its minimum feature set. It should not be used in a production environment!

## Installation

This project is Python based and uses [poetry](https://python-poetry.org/) for
its development.

To create sdist tarball and wheel run

```
poetry build
```

To install the resulting wheel using `pip` run

```
pip install dist/*.whl
```

## Documentation

The user facing documentation of repod can be found in [docs](docs/) and is
built using

```
tox -e docs
```

The documentation is published at [repod.archlinux.page][https://repod.archlinux.page].

## Contributing

Read our [contributing guide](CONTRIBUTING.md) to learn more about how to
provide fixes or improvements for the code and documentation.

## License

Repod's code is licensed under the terms of the **GPL-3.0-or-later** (see
[LICENSE](LICENSE)) and its documentation is licensed under the terms of the
**GFDL-1.3-or-later** (see [docs/LICENSE](docs/LICENSE)).
