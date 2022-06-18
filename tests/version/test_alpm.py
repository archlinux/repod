from unittest.mock import patch

from pytest import mark
from pytest_lazyfixture import lazy_fixture

from repod.version.alpm import pkg_vercmp, vercmp


@mark.parametrize(
    "first, second, expectation",
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
        ("", "", 0),
        ("", "1", -1),
        ("", "a", 1),
    ],
)
@mark.parametrize("pyalpm_vercmp", [lazy_fixture("pyalpm_vercmp_fun")])
def test_vercmp(first: str, second: str, expectation: int, pyalpm_vercmp: bool) -> None:
    with patch("repod.version.alpm.PYALPM_VERCMP", pyalpm_vercmp):
        assert vercmp(a=first, b=second) == expectation


@mark.parametrize(
    "first, second, expectation",
    [
        ("1-2", "1-2", 0),
        ("1:2-3", "2-3", 1),
        ("1:2-3", "1:2-4", -1),
    ],
)
@mark.parametrize("pyalpm_vercmp", [lazy_fixture("pyalpm_vercmp_fun")])
def test_pkgver_vercmp(first: str, second: str, expectation: int, pyalpm_vercmp: bool) -> None:
    with patch("repod.version.alpm.PYALPM_VERCMP", pyalpm_vercmp):
        assert pkg_vercmp(a=first, b=second) == expectation
