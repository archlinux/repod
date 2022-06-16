from typing import Union

from pytest import mark

from repod.version.util import cmp


@mark.parametrize(
    "first, second, expectation",
    [
        ("1", "1", 0),
        ("1", "2", -1),
        ("11", "12", -1),
        ("2", "1", 1),
        ("a", "a", 0),
        ("a", "b", -1),
        ("b", "a", 1),
        ("aa", "ab", -1),
        (1, 1, 0),
        (1, 2, -1),
        (2, 1, 1),
        (12, 11, 1),
    ],
)
def test_cmp(first: Union[int, str], second: Union[int, str], expectation: int) -> None:
    assert cmp(first, second) == expectation
