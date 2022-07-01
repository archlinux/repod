# repod
This project contains tooling to maintain binary package repositories for Linux
distributions using the [pacman](https://archlinux.org/pacman/) package manager.

The latest documentation can be found at
[repod.archlinux.page](https://repod.archlinux.page).

**NOTE**: *Repod is still alpha grade software and as such has not yet reached
its targetted feature set and has not been thoroughly tested in the field. It
should not be used in a production environment!*

## Installation

You can install the latest released version of repod by executing

```
pip install repod
```

## Requirements

When installing repod, its dependencies are automatically installed.

However, the project has a few special dependencies which can be replaced by
other packages, depending on availability.

### Pyalpm

The Python package [pyalpm](https://pypi.org/project/pyalpm/) is not
installable on all operating systems as it depends on the availability of
[libalpm](https://man.archlinux.org/man/libalpm.3) (a C library), which is
usually provided via [pacman](https://man.archlinux.org/man/pacman.8).

However, if `pyalpm` is detected, repod will make use of it for version
comparison instead of a builtin implementation of this functionality, which is
based on [vercmp](https://man.archlinux.org/man/vercmp.8).

### Python-magic

By default the [python-magic](https://pypi.org/project/python-magic/) Python
package is used by repod to detect file types. The detection is based on
`libmagic` (a C library), usually provided via
[file](https://darwinsys.com/file/).

Confusingly, the file project also offers a Python module called `file-magic`,
but it is not available on pypi.org and mostly only found on e.g. Linux
distributions.

If file's `file-magic` Python module is detected, repod will make use of it for
file type detection instead of using `python-magic`.

## Contributing

Read our [contributing guide](CONTRIBUTING.md) to learn more about how to
provide fixes or improvements for the code and documentation.

## License

Repod's code is licensed under the terms of the **GPL-3.0-or-later** (see
[LICENSE](LICENSE)) and its documentation is licensed under the terms of the
**GFDL-1.3-or-later** (see [docs/LICENSE](docs/LICENSE)).
