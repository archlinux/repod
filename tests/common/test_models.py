from contextlib import nullcontext as does_not_raise
from typing import ContextManager, List, Optional, Union
from unittest.mock import patch

from pydantic import ValidationError
from pytest import lazy_fixture, mark, raises

from repod.common import models
from tests.conftest import (
    create_default_full_version,
    create_default_invalid_full_version,
)


@mark.parametrize(
    "builddate, expectation",
    [
        (-1, raises(ValueError)),
        (1, does_not_raise()),
    ],
)
def test_builddate(builddate: int, expectation: ContextManager[str]) -> None:
    with expectation:
        assert builddate == models.BuildDate(builddate=builddate).builddate


@mark.parametrize(
    "csize, expectation",
    [
        (-1, raises(ValueError)),
        (1, does_not_raise()),
    ],
)
def test_csize(csize: int, expectation: ContextManager[str]) -> None:
    with expectation:
        assert csize == models.CSize(csize=csize).csize


@mark.parametrize(
    "value, expectation",
    [
        ("1", does_not_raise()),
        (1, does_not_raise()),
        ("0", raises(ValidationError)),
        ("-1", raises(ValidationError)),
        ("1.1", raises(ValidationError)),
    ],
)
def test_epoch(value: Union[str, int], expectation: ContextManager[str]) -> None:
    with expectation:
        assert isinstance(models.Epoch(epoch=value), models.Epoch)


@mark.parametrize(
    "subj, obj, expectation",
    [
        ("1", "1", 0),
        ("1", "2", -1),
        ("2", "1", 1),
        (1, 1, 0),
        (1, 2, -1),
        (2, 1, 1),
    ],
)
def test_epoch_vercmp(subj: Union[int, str], obj: Union[int, str], expectation: int) -> None:
    assert models.Epoch(epoch=subj).vercmp(epoch=models.Epoch(epoch=obj)) == expectation


@mark.parametrize(
    "file_list, expectation",
    [
        (None, does_not_raise()),
        ([], does_not_raise()),
        (["foo"], does_not_raise()),
        (["home/foo"], raises(ValidationError)),
    ],
)
def test_file_list(file_list: Optional[List[str]], expectation: ContextManager[str]) -> None:
    with expectation:
        models.FileList(files=file_list)


@mark.parametrize(
    "isize, expectation",
    [
        (-1, raises(ValueError)),
        (1, does_not_raise()),
    ],
)
def test_isize(isize: int, expectation: ContextManager[str]) -> None:
    with expectation:
        assert isize == models.ISize(isize=isize).isize


@mark.parametrize(
    "name, expectation",
    [
        (".foo", raises(ValueError)),
        ("-foo", raises(ValueError)),
        ("foo'", raises(ValueError)),
        ("foo", does_not_raise()),
    ],
)
def test_name(name: str, expectation: ContextManager[str]) -> None:
    with expectation:
        assert name == models.Name(name=name).name


def test_packager(default_packager: str, default_invalid_packager: str) -> None:
    with does_not_raise():
        models.Packager(packager=default_packager)
    with raises(ValidationError):
        models.Packager(packager=default_invalid_packager)


@mark.parametrize(
    "value, expectation",
    [
        ("1", does_not_raise()),
        ("1.1", does_not_raise()),
        (1, does_not_raise()),
        (1.1, does_not_raise()),
        ("0", raises(ValidationError)),
        ("-1", raises(ValidationError)),
        ("1.a", raises(ValidationError)),
    ],
)
def test_pkgrel(value: str, expectation: ContextManager[str]) -> None:
    with expectation:
        assert isinstance(models.PkgRel(pkgrel=value), models.PkgRel)


@mark.parametrize(
    "value, expectation",
    [
        ("1", ["1"]),
        ("1.1", ["1", "1"]),
        (1, ["1"]),
        (1.1, ["1", "1"]),
    ],
)
def test_pkgrel_as_list(value: str, expectation: List[str]) -> None:
    assert models.PkgRel(pkgrel=value).as_list() == expectation


@mark.parametrize(
    "subj, obj, expectation",
    [
        ("1", "1", 0),
        ("2", "1", 1),
        ("1", "2", -1),
        ("1", "1.1", -1),
        ("1.1", "1", 1),
        ("1.1", "1.1", 0),
        ("1.2", "1.1", 1),
        ("1.1", "1.2", -1),
    ],
)
@mark.parametrize("pyalpm_vercmp", [lazy_fixture("pyalpm_vercmp_fun")])
def test_pkgrel_vercmp(subj: str, obj: str, expectation: int, pyalpm_vercmp: bool) -> None:
    with patch("repod.version.alpm.PYALPM_VERCMP", pyalpm_vercmp):
        assert models.PkgRel(pkgrel=subj).vercmp(pkgrel=models.PkgRel(pkgrel=obj)) == expectation


@mark.parametrize(
    "value, expectation",
    [
        ("1", does_not_raise()),
        ("1.1", does_not_raise()),
        ("1.a", does_not_raise()),
        (1, does_not_raise()),
        (1.1, does_not_raise()),
        ("0", does_not_raise()),
        ("foo", does_not_raise()),
        ("-1", raises(ValidationError)),
        (".1", raises(ValidationError)),
    ],
)
def test_pkgver(value: str, expectation: ContextManager[str]) -> None:
    with expectation:
        assert isinstance(models.PkgVer(pkgver=value), models.PkgVer)


@mark.parametrize(
    "value, expectation",
    [
        ("1", ["1"]),
        ("1.1", ["1", "1"]),
        ("1.a", ["1", "a"]),
        ("1.1a", ["1", "1a"]),
        ("foo", ["foo"]),
        ("1_1", ["1", "1"]),
        ("1.1_1", ["1", "1", "1"]),
        (1, ["1"]),
        (1.1, ["1", "1"]),
    ],
)
def test_pkgver_as_list(value: str, expectation: List[str]) -> None:
    assert models.PkgVer(pkgver=value).as_list() == expectation


@mark.parametrize(
    "subj, obj, expectation",
    [
        ("1", "1", 0),
        ("2", "1", 1),
        ("1", "2", -1),
        ("1", "1.1", -1),
        ("1.1", "1", 1),
        ("1.1", "1.1", 0),
        ("1.2", "1.1", 1),
        ("1.1", "1.2", -1),
        ("1+2", "1+1", 1),
        ("1+1", "1+2", -1),
        ("1.1", "1.1a", 1),
        ("1.1a", "1.1", -1),
        ("1.1", "1.1a1", 1),
        ("1.1a1", "1.1", -1),
        ("1.1", "1.11a", -1),
        ("1.11a", "1.1", 1),
        ("1.1_a", "1.1", 1),
        ("1.1", "1.1_a", -1),
        ("1.1", "1.1.a", -1),
        ("1.a", "1.1", -1),
        ("1.1", "1.a", 1),
        ("1.a1", "1.1", -1),
        ("1.1", "1.a1", 1),
        ("1.a11", "1.1", -1),
        ("1.1", "1.a11", 1),
        ("a.1", "1.1", -1),
        ("1.1", "a.1", 1),
        ("foo", "1.1", -1),
        ("1.1", "foo", 1),
        ("a1a", "a1b", -1),
        ("a1b", "a1a", 1),
        ("20220102", "20220202", -1),
        ("20220202", "20220102", 1),
        ("1.0..", "1.0.", 0),
        ("1.0.", "1.0", 1),
        ("1..0", "1.0", 1),
        ("1..0", "1..0", 0),
        ("1..0", "1..1", -1),
        ("1.0", "1+0", 0),
        ("1.1a1", "1.111", -1),
        ("01", "1", 0),
        ("001a", "1a", 0),
        ("1.a001a.1", "1.a1a.1", 0),
    ],
)
@mark.parametrize("pyalpm_vercmp", [lazy_fixture("pyalpm_vercmp_fun")])
def test_pkgver_vercmp(subj: str, obj: str, expectation: int, pyalpm_vercmp: bool) -> None:
    with patch("repod.version.alpm.PYALPM_VERCMP", pyalpm_vercmp):
        assert models.PkgVer(pkgver=subj).vercmp(pkgver=models.PkgVer(pkgver=obj)) == expectation


@mark.parametrize(
    "value, expectation",
    [
        (f"{create_default_full_version()}", does_not_raise()),
        (f"{create_default_invalid_full_version()}", raises(ValidationError)),
    ],
)
def test_version(value: str, expectation: ContextManager[str]) -> None:
    with expectation:
        assert isinstance(models.Version(version=value), models.Version)


@mark.parametrize(
    "value, expectation",
    [
        ("1:1.0.0-1", models.Epoch(epoch=1)),
        ("1.0.0-1", None),
    ],
)
def test_version_get_epoch(value: str, expectation: Optional[models.Epoch]) -> None:
    assert models.Version(version=value).get_epoch() == expectation


@mark.parametrize(
    "value, expectation",
    [
        ("1:1.0.0-1", models.PkgVer(pkgver="1.0.0")),
        ("1:1_0_0-1", models.PkgVer(pkgver="1_0_0")),
        ("1.0.0-1", models.PkgVer(pkgver="1.0.0")),
        ("1_0_0-1", models.PkgVer(pkgver="1_0_0")),
    ],
)
def test_version_get_pkgver(value: str, expectation: Optional[models.PkgVer]) -> None:
    assert models.Version(version=value).get_pkgver() == expectation


@mark.parametrize(
    "value, expectation",
    [
        ("1:1.0.0-1", models.PkgRel(pkgrel="1")),
        ("1:1_0_0-1", models.PkgRel(pkgrel="1")),
        ("1.0.0-1", models.PkgRel(pkgrel="1")),
        ("1_0_0-1", models.PkgRel(pkgrel="1")),
        ("1:1.0.0-1.1", models.PkgRel(pkgrel="1.1")),
        ("1:1_0_0-1.1", models.PkgRel(pkgrel="1.1")),
        ("1.0.0-1.1", models.PkgRel(pkgrel="1.1")),
        ("1_0_0-1.1", models.PkgRel(pkgrel="1.1")),
    ],
)
def test_version_get_pkgrel(value: str, expectation: Optional[models.PkgRel]) -> None:
    assert models.Version(version=value).get_pkgrel() == expectation


@mark.parametrize(
    "subj, obj, expectation",
    [
        ("1.0.0-1", "1.0.0-1", 0),
        ("1.0.0-1", "1.0.0-2", -1),
        ("1.0.0-2", "1.0.0-1", 1),
        ("1.0.1-1", "1.0.0-1", 1),
        ("1.0.0-1", "1.0.1-1", -1),
        ("1:1.0.0-1", "1:1.0.0-1", 0),
        ("1:1.0.0-1", "1:1.0.0-2", -1),
        ("1:1.0.0-2", "1:1.0.0-1", 1),
        ("1:1.0.1-1", "1:1.0.0-1", 1),
        ("1:1.0.0-1", "1:1.0.1-1", -1),
        ("2:1.0.0-1", "1:1.0.0-1", 1),
        ("1:1.0.0-1", "2:1.0.1-1", -1),
        ("1:1.0.0-1", "1.0.0-1", 1),
        ("1.0.0-1", "1:1.0.0-1", -1),
    ],
)
@mark.parametrize("pyalpm_vercmp", [lazy_fixture("pyalpm_vercmp_fun")])
def test_version_vercmp(subj: str, obj: str, expectation: int, pyalpm_vercmp: bool) -> None:
    with patch("repod.version.alpm.PYALPM_VERCMP", pyalpm_vercmp):
        assert models.Version(version=subj).vercmp(version=models.Version(version=obj)) == expectation


@mark.parametrize(
    "subj, obj, expectation",
    [
        ("1.2.3-1", "1.2.3-2", True),
        ("1.2.3-2", "1.2.3-1", False),
    ],
)
def test_version_is_older_than(subj: str, obj: str, expectation: bool) -> None:
    assert models.Version(version=subj).is_older_than(version=models.Version(version=obj)) is expectation


@mark.parametrize(
    "subj, obj, expectation",
    [
        ("1.2.3-1", "1.2.3-2", False),
        ("1.2.3-2", "1.2.3-1", True),
    ],
)
def test_version_is_newer_than(subj: str, obj: str, expectation: bool) -> None:
    assert models.Version(version=subj).is_newer_than(version=models.Version(version=obj)) is expectation
